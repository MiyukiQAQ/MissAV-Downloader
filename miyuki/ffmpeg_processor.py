import subprocess
from typing import Optional
from miyuki.config import FFMPEG_INPUT_FILE
from miyuki.logger import logger


class FFmpegProcessor:
    @staticmethod
    def create_video_from_segments(segment_files: list[str], output_file: str, cover_file: Optional[str] = None) -> None:
        with open(FFMPEG_INPUT_FILE, 'w') as f:
            for file in segment_files:
                f.write(f"file '{file}'\n")
        ffmpeg_command = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', FFMPEG_INPUT_FILE]
        if cover_file:
            ffmpeg_command.extend(['-i', cover_file, '-map', '0', '-map', '1', '-c', 'copy', '-disposition:v:1', 'attached_pic'])
        else:
            ffmpeg_command.extend(['-c', 'copy'])
        ffmpeg_command.append(output_file)
        try:
            subprocess.run(ffmpeg_command, check=True, stdout=subprocess.DEVNULL)
            logger.info("FFmpeg execution completed.")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg execution failed: {e}")
            raise
