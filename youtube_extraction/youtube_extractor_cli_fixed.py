#!/usr/bin/env python3
"""
🎬 EXTRATOR DE VÍDEOS DO YOUTUBE - SISTEMA ORGANIZADO
====================================================
Sistema completo para extração de vídeos do YouTube com:
- Extração por vídeo individual ou playlist completa
- Organização em subpastas por vídeo (com controle de versão)
- Geração automática de .zip com todo conteúdo
- Interface de linha de comando
- Estrutura organizada de armazenamento
"""

import os
import sys
import json
import shutil
import zipfile
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import subprocess
import time

# Imports para YouTube
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    print("❌ yt-dlp não instalado. Execute: pip install yt-dlp")
    YT_DLP_AVAILABLE = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YOUTUBE_TRANSCRIPT_AVAILABLE = True
except ImportError:
    print("❌ youtube-transcript-api não instalado. Execute: pip install youtube-transcript-api")
    YOUTUBE_TRANSCRIPT_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    print("❌ requests/beautifulsoup4 não instalados. Execute: pip install requests beautifulsoup4")
    WEB_SCRAPING_AVAILABLE = False

class YouTubeExtractorOrganized:
    """
    🎬 Extrator organizado de vídeos do YouTube
    """
    
    def __init__(self, storage_dir: str = "storage"):
        """
        Inicializa o extrator de vídeos do YouTube
        
        Args:
            storage_dir: Diretório principal de armazenamento
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Arquivo ZIP principal
        self.zip_file = self.storage_dir / "all_extracted_videos.zip"
        
        print(f"🎬 YouTubeExtractorOrganized inicializado")
        print(f"📁 Diretório de armazenamento: {self.storage_dir}")
        print(f"📦 Arquivo ZIP: {self.zip_file}")
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extrai ID do vídeo de URL do YouTube
        
        Args:
            url: URL do YouTube
            
        Returns:
            ID do vídeo ou None se inválido
        """
        try:
            patterns = [
                r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
                r'youtube\.com/v/([^&\n?#]+)',
                r'youtube\.com/watch\?.*v=([^&\n?#]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            # Se já for um ID
            if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
                return url
                
            return None
            
        except Exception as e:
            print(f"❌ Erro ao extrair ID do vídeo: {e}")
            return None
    
    def extract_playlist_id(self, url: str) -> Optional[str]:
        """
        Extrai ID da playlist de URL do YouTube
        
        Args:
            url: URL da playlist do YouTube
            
        Returns:
            ID da playlist ou None se inválido
        """
        try:
            patterns = [
                r'list=([^&\n?#]+)',
                r'playlist\?list=([^&\n?#]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
                    
            return None
            
        except Exception as e:
            print(f"❌ Erro ao extrair ID da playlist: {e}")
            return None
    
    def get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        """
        Obtém metadados do vídeo usando yt-dlp
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Metadados do vídeo
        """
        if not YT_DLP_AVAILABLE:
            return {'error': 'yt-dlp não disponível'}
        
        try:
            url = f'https://www.youtube.com/watch?v={video_id}'
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                metadata = {
                    'video_id': video_id,
                    'title': info.get('title', ''),
                    'description': info.get('description', ''),
                    'uploader': info.get('uploader', ''),
                    'upload_date': info.get('upload_date', ''),
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'url': url,
                    'extraction_date': datetime.now().isoformat()
                }
                
                return metadata
            
        except Exception as e:
            print(f"❌ Erro ao obter metadados: {e}")
            return {
                'video_id': video_id,
                'title': f'Video_{video_id}',
                'error': str(e),
                'extraction_date': datetime.now().isoformat()
            }
    
    def get_playlist_videos(self, playlist_id: str) -> List[str]:
        """
        Obtém lista de vídeos de uma playlist
        
        Args:
            playlist_id: ID da playlist
            
        Returns:
            Lista de IDs de vídeos
        """
        if not YT_DLP_AVAILABLE:
            return []
        
        try:
            url = f'https://www.youtube.com/playlist?list={playlist_id}'
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                playlist_info = ydl.extract_info(url, download=False)
                
                video_ids = []
                for entry in playlist_info.get('entries', []):
                    if entry and entry.get('id'):
                        video_ids.append(entry['id'])
                
                print(f"📋 Playlist {playlist_id}: {len(video_ids)} vídeos encontrados")
                return video_ids
        
        except Exception as e:
            print(f"❌ Erro ao obter vídeos da playlist: {e}")
            return []
    
    def get_transcript(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém transcrição do vídeo
        
        Args:
            video_id: ID do vídeo
            
        Returns:
            Dados da transcrição ou None
        """
        if not YOUTUBE_TRANSCRIPT_AVAILABLE:
            return None
        
        try:
            transcript_list = YouTubeTranscriptApi.list(video_id)
            
            # Tentar idiomas preferidos
            languages = ['pt', 'pt-BR', 'en', 'es']
            transcript = None
            
            try:
                # Tentar manual primeiro
                transcript = transcript_list.find_manually_created_transcript(languages)
            except:
                try:
                    # Tentar gerada
                    transcript = transcript_list.find_generated_transcript(languages)
                except:
                    # Pegar qualquer uma disponível
                    if transcript_list:
                        transcript = list(transcript_list)[0]
            
            if not transcript:
                return None
            
            # Obter dados da transcrição
            transcript_data = transcript.fetch()
            
            # Processar segmentos
            segments = []
            full_text = ""
            
            for i, segment in enumerate(transcript_data):
                segment_info = {
                    'index': i,
                    'text': segment['text'].strip(),
                    'start': segment['start'],
                    'duration': segment['duration'],
                    'end': segment['start'] + segment['duration']
                }
                segments.append(segment_info)
                full_text += segment['text'] + " "
            
            return {
                'video_id': video_id,
                'language': transcript.language_code,
                'is_generated': transcript.is_generated,
                'segments': segments,
                'full_text': full_text.strip(),
                'total_segments': len(segments),
                'extraction_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Erro ao obter transcrição: {e}")
            return None
    
    def create_video_folder_name(self, title: str, video_id: str) -> str:
        """
        Cria nome da pasta do vídeo (primeiros 20 caracteres do título)
        
        Args:
            title: Título do vídeo
            video_id: ID do vídeo
            
        Returns:
            Nome da pasta
        """
        try:
            # Limpar título
            clean_title = re.sub(r'[<>:"/\\|?*]', '', title)
            clean_title = clean_title.strip()
            
            # Primeiros 20 caracteres
            if len(clean_title) > 20:
                folder_name = clean_title[:20].strip()
            else:
                folder_name = clean_title
            
            # Se ficou vazio, usar ID
            if not folder_name:
                folder_name = video_id[:11]
            
            return folder_name
            
        except:
            return video_id[:11]
    
    def get_next_version_folder(self, base_folder_name: str) -> str:
        """
        Obtém próxima versão da pasta (controle de versão)
        
        Args:
            base_folder_name: Nome base da pasta
            
        Returns:
            Nome da pasta com versão
        """
        version = 1
        folder_name = base_folder_name
        
        while (self.storage_dir / folder_name).exists():
            version += 1
            folder_name = f"{base_folder_name}_v{version}"
        
        return folder_name
    
    def download_thumbnail(self, video_id: str, thumbnail_url: str, output_dir: Path) -> Optional[str]:
        """
        Baixa thumbnail do vídeo
        
        Args:
            video_id: ID do vídeo
            thumbnail_url: URL da thumbnail
            output_dir: Diretório de saída
            
        Returns:
            Caminho da thumbnail ou None
        """
        if not WEB_SCRAPING_AVAILABLE or not thumbnail_url:
            return None
        
        try:
            response = requests.get(thumbnail_url, timeout=10)
            response.raise_for_status()
            
            thumbnail_path = output_dir / f"{video_id}_thumbnail.jpg"
            
            with open(thumbnail_path, 'wb') as f:
                f.write(response.content)
            
            return str(thumbnail_path)
            
        except Exception as e:
            print(f"⚠️ Não foi possível baixar thumbnail: {e}")
            return None
    
    def extract_single_video(self, url_or_id: str) -> Dict[str, Any]:
        """
        Extrai dados de um único vídeo
        
        Args:
            url_or_id: URL ou ID do vídeo
            
        Returns:
            Resultado da extração
        """
        try:
            print(f"\n🎬 Processando vídeo: {url_or_id}")
            
            # Extrair ID do vídeo
            video_id = self.extract_video_id(url_or_id)
            if not video_id:
                return {'error': 'ID do vídeo inválido', 'input': url_or_id}
            
            print(f"📹 ID do vídeo: {video_id}")
            
            # Obter metadados
            print("📊 Obtendo metadados...")
            metadata = self.get_video_metadata(video_id)
            
            if 'error' in metadata:
                return {'error': f"Erro ao obter metadados: {metadata['error']}", 'video_id': video_id}
            
            # Criar nome da pasta
            base_folder_name = self.create_video_folder_name(metadata['title'], video_id)
            folder_name = self.get_next_version_folder(base_folder_name)
            video_folder = self.storage_dir / folder_name
            video_folder.mkdir(exist_ok=True)
            
            print(f"📁 Pasta criada: {folder_name}")
            
            # Salvar metadados
            metadata_file = video_folder / f"{video_id}_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # Obter transcrição
            print("📝 Extraindo transcrição...")
            transcript = self.get_transcript(video_id)
            
            if transcript:
                transcript_file = video_folder / f"{video_id}_transcript.json"
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    json.dump(transcript, f, ensure_ascii=False, indent=2)
                
                # Salvar texto puro
                text_file = video_folder / f"{video_id}_text.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(transcript['full_text'])
                
                print(f"✅ Transcrição extraída: {len(transcript['segments'])} segmentos")
            else:
                print("⚠️ Transcrição não disponível")
            
            # Baixar thumbnail
            print("🖼️ Baixando thumbnail...")
            thumbnail_path = self.download_thumbnail(
                video_id, 
                metadata.get('thumbnail', ''), 
                video_folder
            )
            
            # Criar resumo
            summary = {
                'video_id': video_id,
                'folder_name': folder_name,
                'title': metadata['title'],
                'duration': metadata.get('duration', 0),
                'has_transcript': transcript is not None,
                'has_thumbnail': thumbnail_path is not None,
                'extraction_date': datetime.now().isoformat(),
                'files_created': {
                    'metadata': str(metadata_file),
                    'transcript': str(transcript_file) if transcript else None,
                    'text': str(text_file) if transcript else None,
                    'thumbnail': thumbnail_path
                }
            }
            
            summary_file = video_folder / f"{video_id}_summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Vídeo processado com sucesso!")
            print(f"📁 Pasta: {folder_name}")
            print(f"📊 Duração: {metadata.get('duration', 0) / 60:.1f} minutos")
            
            return {
                'success': True,
                'video_id': video_id,
                'folder_name': folder_name,
                'folder_path': str(video_folder),
                'summary': summary
            }
            
        except Exception as e:
            print(f"❌ Erro ao processar vídeo: {e}")
            return {'error': str(e), 'input': url_or_id}
    
    def extract_playlist(self, playlist_url: str) -> Dict[str, Any]:
        """
        Extrai todos os vídeos de uma playlist
        
        Args:
            playlist_url: URL da playlist
            
        Returns:
            Resultado da extração
        """
        try:
            print(f"\n📋 Processando playlist: {playlist_url}")
            
            # Extrair ID da playlist
            playlist_id = self.extract_playlist_id(playlist_url)
            if not playlist_id:
                return {'error': 'ID da playlist inválido', 'input': playlist_url}
            
            print(f"📋 ID da playlist: {playlist_id}")
            
            # Obter vídeos da playlist
            video_ids = self.get_playlist_videos(playlist_id)
            if not video_ids:
                return {'error': 'Nenhum vídeo encontrado na playlist', 'playlist_id': playlist_id}
            
            print(f"🎬 {len(video_ids)} vídeos para processar")
            
            # Processar cada vídeo
            results = []
            success_count = 0
            error_count = 0
            
            for i, video_id in enumerate(video_ids, 1):
                print(f"\n[{i}/{len(video_ids)}] Processando vídeo: {video_id}")
                
                result = self.extract_single_video(f"https://www.youtube.com/watch?v={video_id}")
                results.append(result)
                
                if result.get('success'):
                    success_count += 1
                else:
                    error_count += 1
                
                # Pausa entre vídeos para evitar rate limiting
                if i < len(video_ids):
                    time.sleep(1)
            
            # Salvar relatório da playlist
            playlist_report = {
                'playlist_id': playlist_id,
                'playlist_url': playlist_url,
                'total_videos': len(video_ids),
                'successful_extractions': success_count,
                'failed_extractions': error_count,
                'extraction_date': datetime.now().isoformat(),
                'video_results': results
            }
            
            report_file = self.storage_dir / f"playlist_{playlist_id}_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(playlist_report, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ Playlist processada!")
            print(f"📊 Sucessos: {success_count}")
            print(f"❌ Erros: {error_count}")
            print(f"📄 Relatório: {report_file}")
            
            return {
                'success': True,
                'playlist_id': playlist_id,
                'total_videos': len(video_ids),
                'successful_extractions': success_count,
                'failed_extractions': error_count,
                'report_file': str(report_file),
                'results': results
            }
            
        except Exception as e:
            print(f"❌ Erro ao processar playlist: {e}")
            return {'error': str(e), 'input': playlist_url}
    
    def create_zip_archive(self) -> str:
        """
        Cria/atualiza arquivo ZIP com todo conteúdo extraído
        
        Returns:
            Caminho do arquivo ZIP
        """
        try:
            print(f"\n📦 Criando arquivo ZIP: {self.zip_file}")
            
            # Remover ZIP anterior se existir
            if self.zip_file.exists():
                self.zip_file.unlink()
            
            # Criar novo ZIP
            with zipfile.ZipFile(self.zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Adicionar todas as pastas e arquivos
                for item in self.storage_dir.iterdir():
                    if item.is_dir():
                        # Adicionar pasta completa
                        for file_path in item.rglob('*'):
                            if file_path.is_file():
                                # Caminho relativo dentro do ZIP
                                arc_path = file_path.relative_to(self.storage_dir)
                                zipf.write(file_path, arc_path)
                    elif item.is_file() and item != self.zip_file:
                        # Adicionar arquivos na raiz (relatórios de playlist)
                        zipf.write(item, item.name)
            
            zip_size = self.zip_file.stat().st_size / 1024 / 1024  # MB
            print(f"✅ Arquivo ZIP criado: {self.zip_file}")
            print(f"📦 Tamanho: {zip_size:.1f} MB")
            
            return str(self.zip_file)
            
        except Exception as e:
            print(f"❌ Erro ao criar ZIP: {e}")
            return ""
    
    def list_extracted_videos(self) -> List[Dict[str, Any]]:
        """
        Lista todos os vídeos extraídos
        
        Returns:
            Lista de vídeos extraídos
        """
        videos = []
        
        try:
            for item in self.storage_dir.iterdir():
                if item.is_dir():
                    # Procurar arquivo de resumo
                    summary_files = list(item.glob('*_summary.json'))
                    if summary_files:
                        try:
                            with open(summary_files[0], 'r', encoding='utf-8') as f:
                                summary = json.load(f)
                                videos.append(summary)
                        except:
                            continue
            
            return sorted(videos, key=lambda x: x.get('extraction_date', ''), reverse=True)
            
        except Exception as e:
            print(f"❌ Erro ao listar vídeos: {e}")
            return []

def main():
    """
    Interface de linha de comando
    """
    parser = argparse.ArgumentParser(
        description='🎬 Extrator de Vídeos do YouTube - Sistema Organizado',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:

  # Extrair um vídeo
  python youtube_extractor_cli.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
  
  # Extrair playlist completa
  python youtube_extractor_cli.py --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID"
  
  # Listar vídeos extraídos
  python youtube_extractor_cli.py --list
  
  # Criar arquivo ZIP
  python youtube_extractor_cli.py --zip
"""
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--url', '-u', help='URL do vídeo do YouTube')
    group.add_argument('--playlist', '-p', help='URL da playlist do YouTube')
    group.add_argument('--list', '-l', action='store_true', help='Listar vídeos extraídos')
    group.add_argument('--zip', '-z', action='store_true', help='Criar arquivo ZIP')
    
    parser.add_argument('--storage', '-s', default='storage', help='Diretório de armazenamento (padrão: storage)')
    
    args = parser.parse_args()
    
    # Criar extrator
    extractor = YouTubeExtractorOrganized(args.storage)
    
    try:
        if args.url:
            # Extrair vídeo único
            result = extractor.extract_single_video(args.url)
            
            if result.get('success'):
                print(f"\n🎉 Extração concluída com sucesso!")
                # Criar ZIP automaticamente
                zip_path = extractor.create_zip_archive()
                if zip_path:
                    print(f"📦 Arquivo ZIP atualizado: {zip_path}")
            else:
                print(f"\n❌ Erro na extração: {result.get('error')}")
                sys.exit(1)
        
        elif args.playlist:
            # Extrair playlist
            result = extractor.extract_playlist(args.playlist)
            
            if result.get('success'):
                print(f"\n🎉 Playlist extraída com sucesso!")
                print(f"📊 {result['successful_extractions']}/{result['total_videos']} vídeos processados")
                # Criar ZIP automaticamente
                zip_path = extractor.create_zip_archive()
                if zip_path:
                    print(f"📦 Arquivo ZIP atualizado: {zip_path}")
            else:
                print(f"\n❌ Erro na extração da playlist: {result.get('error')}")
                sys.exit(1)
        
        elif args.list:
            # Listar vídeos
            videos = extractor.list_extracted_videos()
            
            if videos:
                print(f"\n📹 Vídeos extraídos ({len(videos)} total):")
                print("=" * 60)
                
                for i, video in enumerate(videos, 1):
                    duration_min = video.get('duration', 0) / 60
                    print(f"{i:2d}. {video['title'][:40]}...")
                    print(f"    📁 {video['folder_name']}")
                    print(f"    ⏱️ {duration_min:.1f}min | 📝 {'✅' if video.get('has_transcript') else '❌'} | 🖼️ {'✅' if video.get('has_thumbnail') else '❌'}")
                    print(f"    📅 {video.get('extraction_date', '')[:19]}")
                    print()
            else:
                print("\n📹 Nenhum vídeo extraído ainda.")
        
        elif args.zip:
            # Criar ZIP
            zip_path = extractor.create_zip_archive()
            
            if zip_path:
                print(f"\n✅ Arquivo ZIP criado: {zip_path}")
            else:
                print(f"\n❌ Erro ao criar arquivo ZIP")
                sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n\n⚠️ Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
