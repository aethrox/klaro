import os
from langchain.tools import tool

# Proje analizi için dikkate alınması gereken yaygın kod ve önemli konfigürasyon dosyaları.
IMPORTANT_EXTENSIONS = ('.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.md', '.json', '.yaml', '.yml', '.toml')
IMPORTANT_FILES = ('requirements.txt', 'package.json', 'Dockerfile', 'LICENSE', '.gitignore', 'klaro_project_plan')

@tool
def list_files(directory: str = ".") -> str:
    """
    Belirtilen dizin içindeki tüm önemli kod ve konfigürasyon dosyalarını listeler.
    Ajana proje yapısını anlaması için genel bir bakış sağlar.
    
    Yalnızca önemli uzantılara sahip dosyaları ve belirlenmiş önemli dosyaları döndürür.
    '.' ile başlayan gizli klasörleri (örneğin '.git', '.venv') yoksayar.

    Args:
        directory (str): Listelenecek dizin yolu. Varsayılan olarak mevcut dizindir (.).

    Returns:
        str: Proje yapısını gösteren, alt dizinleri ve önemli dosyaları içeren biçimlendirilmiş liste.
             Hata durumunda hata mesajı döndürülür.
    """
    if not os.path.isdir(directory):
        return f"Hata: Belirtilen dizin bulunamadı veya geçerli bir dizin değil: {directory}"

    file_list = []
    
    # os.walk kullanarak alt dizinleri gez
    for root, dirs, files in os.walk(directory):
        # Gizli dizinleri (örn. .git, .venv, __pycache__) atla
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('venv', 'node_modules', '__pycache__')]

        for file in files:
            # Dosya uzantısını ve temel dosya adını al
            _, ext = os.path.splitext(file)
            
            # Tam dosya yolu (ajanın read_file ile kullanacağı)
            full_path = os.path.join(root, file)
            # Ajana gösterilecek göreceli yol
            relative_path = os.path.relpath(full_path, start=directory)
            
            # Önemli dosyaları ve uzantıları filtrele
            is_important_file = file in IMPORTANT_FILES
            is_important_extension = ext.lower() in IMPORTANT_EXTENSIONS
            
            if is_important_file or is_important_extension:
                file_list.append(relative_path)

    if not file_list:
        return f"Hata: Dizin ({directory}) içinde analiz için önemli bir dosya bulunamadı."
        
    # Listeyi alfabetik olarak sırala ve yeni satırlarla birleştir
    return "\n".join(sorted(file_list))

@tool
def read_file(file_path: str) -> str:
    """
    Belirtilen bir dosya yolunun içeriğini okur ve döndürür.
    Bu araç, CodebaseReaderTool tarafından listelenen dosyalardan bilgi almak için kullanılır.

    Args:
        file_path (str): Okunacak dosyanın yolu.

    Returns:
        str: Dosyanın içeriği veya hata mesajı.
    """
    try:
        # Dosyaları UTF-8 ile okumayı dene
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # İçeriği LLM'in bağlam penceresini aşmaması için 5000 karakterle sınırla.
        # Daha uzun dosyalar için ajanın sadece önemli kısmı istemesi teşvik edilir.
        if len(content) > 5000:
            return f"UYARI: Dosya çok uzun. Yalnızca ilk 5000 karakter okunmuştur. Toplam uzunluk: {len(content)} karakter.\n\n" + content[:5000]
        
        return content

    except FileNotFoundError:
        return f"Hata: Dosya bulunamadı: {file_path}"
    except UnicodeDecodeError:
        return f"Hata: Dosya içeriği UTF-8 olarak okunamadı. Dosya ikili (binary) olabilir: {file_path}"
    except Exception as e:
        return f"Dosya okuma hatası: {e}"