import os
from pathlib import Path
from typing import Dict, List, Literal, Optional

import requests
import torch
from loguru import logger

_original_torch_load = torch.load


def _safe_torch_load(*args, **kwargs):
    kwargs["weights_only"] = False
    return _original_torch_load(*args, **kwargs)


torch.load = _safe_torch_load

try:
    import whisperx
    from whisperx.diarize import DiarizationPipeline

    HAS_LOCAL_DEPS = True
except ImportError:
    HAS_LOCAL_DEPS = False


class TranscriptionError(Exception):
    pass


class AudioTranscriber:
    def __init__(
        self,
        mode: Literal["local", "cloud"] = "local",
        api_key: Optional[str] = None,
        hf_token: Optional[str] = None,
        device: str = "cuda",
        output_dir: str = "data/processing",
    ):
        """
        初始化转录器
        :param mode: 'local' (WhisperX) 或 'cloud' (Deepgram)
        :param api_key: 云端模式的 API Key (Deepgram Key)
        :param hf_token: 本地模式 Diarization 必须的 HuggingFace Token
        """
        self.mode = mode
        self.api_key = api_key
        self.hf_token = hf_token
        self.device = device
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"[Transcriber] 初始化完成 | 模式: {self.mode} | 设备: {self.device}")

    def transcribe(self, audio_path: str, language: str = "auto") -> List[Dict]:
        """
        主入口：将音频转换为带有说话人的文本片段
        :param audio_path: 本地音频文件的路径
        :param language: 语言代码 ('zh', 'en', 'auto')
        :return: 结构化列表 [{'start': 0.5, 'end': 2.0, 'text': '...', 'speaker': 'SPEAKER_01'}]
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        logger.info(f"[Transcriber] 开始处理: {audio_path} (Lang: {language})")

        try:
            if self.mode == "local":
                return self._transcribe_local_whisperx(audio_path)
            elif self.mode == "cloud":
                return self._transcribe_cloud_deepgram(audio_path, language=language)
            else:
                raise ValueError(f"不支持的模式: {self.mode}")
        except Exception as e:
            logger.exception("[Transcriber] 转录失败")
            raise TranscriptionError(str(e)) from e

    def _transcribe_local_whisperx(self, audio_path: str) -> List[Dict]:
        if not HAS_LOCAL_DEPS:
            raise ImportError("未安装 whisperx 或 torch，无法使用本地模式。请运行 uv add git+https://github.com/m-bain/whisperX.git")

        if not self.hf_token:
            logger.warning("⚠️ 未提供 HuggingFace Token，无法进行说话人分离 (Diarization)，仅能转录文字。")

        # 1. 加载模型
        model_name = "medium"
        compute_type = "int8" if self.device == "cuda" else "int8"
        logger.info(f"⏳ [Local] 正在加载 Whisper 模型 ({model_name}, {compute_type})...")
        model = whisperx.load_model(model_name, self.device, compute_type=compute_type)

        # 2. 转录
        logger.info("[Local] 正在转录文本...")
        result = model.transcribe(audio_path, batch_size=4)

        # 3. 对齐
        logger.info("[Local] 正在对齐时间轴...")
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=self.device)
        result = whisperx.align(result["segments"], model_a, metadata, audio_path, self.device, return_char_alignments=False)

        # 4. 说话人分离
        if self.hf_token:
            logger.info("[Local] 正在识别说话人 (Diarization)...")
            diarize_model = DiarizationPipeline(use_auth_token=self.hf_token, device=self.device)
            diarize_segments = diarize_model(audio_path)

            result = whisperx.assign_word_speakers(diarize_segments, result)

        # 5. 格式化输出
        final_segments = []
        for segment in result["segments"]:
            final_segments.append(
                {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "speaker": segment.get("speaker", "Unknown"),
                }
            )

        logger.success(f"✅ [Local] 转录完成，共 {len(final_segments)} 条片段")
        return final_segments

    def _transcribe_cloud_deepgram(self, audio_path: str, language: str = "auto") -> List[Dict]:
        if not self.api_key:
            raise ValueError("使用 Deepgram 模式必须提供 api_key")

        url = "https://api.deepgram.com/v1/listen"

        # 1. 准备参数
        params = {
            "model": "nova-2",
            "smart_format": "true",  # 自动标点、大小写
            "diarize": "true",  # 开启说话人分离
            "punctuate": "true",
            "utterances": "true",
        }

        # 语言设置
        if language and language != "auto":
            params["language"] = language
        else:
            params["detect_language"] = "true"

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "audio/*",
        }

        logger.info(f"[Deepgram] 开始上传并转录 (语言: {language})...")

        # 2. 发送请求
        try:
            with open(audio_path, "rb") as audio_file:
                response = requests.post(
                    url,
                    params=params,
                    headers=headers,
                    data=audio_file,
                    timeout=600,  # 10分钟超时，防止超大文件断连
                )
        except Exception as e:
            raise TranscriptionError(f"Deepgram 请求失败: {e}")
        if response.status_code != 200:
            raise TranscriptionError(f"Deepgram API 报错 ({response.status_code}): {response.text}")
        data = response.json()

        # 3. 解析结果
        final_segments = []

        try:
            if "paragraphs" in data["results"]["channels"][0]["alternatives"][0]:
                paragraphs = data["results"]["channels"][0]["alternatives"][0]["paragraphs"]["paragraphs"]

                for p in paragraphs:
                    speaker_id = p.get("speaker", 0)
                    sentences = p["sentences"]
                    full_text = " ".join([s["text"] for s in sentences])
                    start_time = sentences[0]["start"]
                    end_time = sentences[-1]["end"]

                    final_segments.append({"start": start_time, "end": end_time, "text": full_text.strip(), "speaker": f"Speaker_{speaker_id}"})
            else:
                utterances = data["results"]["channels"][0]["alternatives"][0]["utterances"]
                for utt in utterances:
                    final_segments.append({"start": utt["start"], "end": utt["end"], "text": utt["transcript"].strip(), "speaker": f"Speaker_{utt.get('speaker', 0)}"})

        except KeyError:
            logger.warning("Deepgram 返回了空结果或格式异常 (可能是静音文件)")
            return []
        except Exception as e:
            raise TranscriptionError(f"解析 Deepgram 结果失败: {e}")

        logger.success(f"[Deepgram] 转录完成，共 {len(final_segments)} 个段落")
        return final_segments
