import importlib.util
import os
from typing import Dict, List, Literal, Optional

import requests
from loguru import logger

HAS_WHISPERX = importlib.util.find_spec("whisperx") is not None
HAS_FUNASR = importlib.util.find_spec("funasr") is not None


# 补丁函数
def _apply_torch_monkey_patch():
    import torch

    if getattr(torch, "_audigest_patched", False):
        return
    logger.debug("🔧 [Local] 应用 PyTorch 兼容性补丁...")
    _original_torch_load = torch.load

    def _safe_torch_load(*args, **kwargs):
        kwargs["weights_only"] = False
        return _original_torch_load(*args, **kwargs)

    torch.load = _safe_torch_load
    setattr(torch, "_audigest_patched", True)


class TranscriptionError(Exception):
    pass


class AudioTranscriber:
    def __init__(
        self,
        mode: Literal["local", "cloud"] = "local",
        api_key: Optional[str] = None,
        hf_token: Optional[str] = None,
        device: Optional[str] = None,
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
        logger.info(f"[Transcriber] 初始化完成 | 模式: {self.mode} | 设备: {self.device}")

    def transcribe(self, audio_path: str, language: str = "auto") -> List[Dict]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        logger.info(f"[Transcriber] 开始处理: {audio_path} (Lang: {language})")

        try:
            if self.mode == "local":
                if language == "zh":
                    logger.info("🇨🇳 检测到中文，切换至 FunASR 引擎...")
                    return self._transcribe_local_funasr(audio_path)
                else:
                    logger.info("🌐 非中文内容，使用 WhisperX 引擎...")
                    return self._transcribe_local_whisperx(audio_path)
            elif self.mode == "cloud":
                return self._transcribe_cloud_deepgram(audio_path, language=language)
            else:
                raise ValueError(f"不支持的模式: {self.mode}")
        except Exception as e:
            logger.exception("❌ [Transcriber] 转录失败")
            raise TranscriptionError(str(e)) from e

    def _transcribe_local_whisperx(self, audio_path: str) -> List[Dict]:
        if not HAS_WHISPERX:
            raise ImportError("未安装 whisperx 或 torch，无法使用本地模式。请运行 uv add git+https://github.com/m-bain/whisperX.git")
        if not self.hf_token:
            logger.warning("⚠️ 未提供 HuggingFace Token，无法进行说话人分离 (Diarization)，仅能转录文字。")
        _apply_torch_monkey_patch()
        import torch
        import whisperx
        from whisperx.diarize import DiarizationPipeline

        actual_device = self.device
        if actual_device is None:
            actual_device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"🖥️ [Auto] 自动检测到运行设备: {actual_device}")

        model_name = "medium"
        compute_type = "int8" if actual_device == "cuda" else "int8"
        logger.info(f"⏳ [Local] 正在加载 Whisper 模型 ({model_name}, {compute_type})...")
        model = whisperx.load_model(model_name, actual_device, compute_type=compute_type)
        logger.info("[Local] 正在转录文本...")
        result = model.transcribe(audio_path, batch_size=4)
        logger.info("[Local] 正在对齐时间轴...")
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=actual_device)
        result = whisperx.align(result["segments"], model_a, metadata, audio_path, actual_device, return_char_alignments=False)
        if self.hf_token:
            logger.info("[Local] 正在识别说话人 (Diarization)...")
            diarize_model = DiarizationPipeline(use_auth_token=self.hf_token, device=actual_device)
            diarize_segments = diarize_model(audio_path)

            result = whisperx.assign_word_speakers(diarize_segments, result)
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

    def _transcribe_local_funasr(self, audio_path: str) -> List[Dict]:
        if not HAS_FUNASR:
            raise ImportError("未安装 funasr。请运行 uv add funasr modelscope")
        try:
            from funasr import AutoModel
        except ImportError:
            raise ImportError("FunASR 导入失败")
        logger.info("⏳ [FunASR] 正在加载模型 (Paraformer-zh + Cam++)...")
        import torch

        actual_device = self.device
        if actual_device is None:
            actual_device = "cuda" if torch.cuda.is_available() else "cpu"

        model = AutoModel(
            model="paraformer-zh",
            model_revision="v2.0.4",
            vad_model="fsmn-vad",
            punc_model="ct-punc",
            spk_model="cam++",
            disable_update=True,
            device=actual_device,
        )

        logger.info("🗣️ [FunASR] 开始转录...")

        try:
            res = model.generate(
                input=audio_path,
                batch_size_s=300,  # 300秒音频一批，显存不够改小
                return_spk_res=True,
            )
        except Exception as e:
            raise TranscriptionError(f"FunASR 推理错误: {e}")

        final_segments = []
        for item in res:
            if "sentence_info" in item:
                for sent in item["sentence_info"]:
                    spk_id = sent.get("spk", 0)

                    final_segments.append(
                        {
                            "start": sent["start"] / 1000.0,  # 毫秒 -> 秒
                            "end": sent["end"] / 1000.0,
                            "text": sent["text"],
                            "speaker": f"Speaker_{spk_id}",
                        }
                    )
        logger.success(f"✅ [FunASR] 中文转录完成，共 {len(final_segments)} 条")
        return final_segments

    def _transcribe_cloud_deepgram(self, audio_path: str, language: str = "auto") -> List[Dict]:
        if not self.api_key:
            raise ValueError("使用 Deepgram 模式必须提供 api_key")

        url = "https://api.deepgram.com/v1/listen"
        params = {
            "model": "nova-2",
            "smart_format": "true",
            "diarize": "true",  # 开启说话人分离
            "punctuate": "true",
            "utterances": "true",
        }
        if language and language != "auto":
            params["language"] = language
        else:
            params["detect_language"] = "true"

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "audio/*",
        }

        logger.info(f"[Deepgram] 开始上传并转录 (语言: {language})...")

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
