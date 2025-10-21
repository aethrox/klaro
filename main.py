import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from prompts import README_PROMPT
from tools import CodeReaderTool

def get_code_content(file_path: str) -> dict:
    """
    Bir ara fonksiyon: Sadece dosya içeriğini okur ve bir sözlük (dictionary) olarak döndürür.
    Bu, LangChain Expression Language (LCEL) ile daha uyumlu çalışır.
    """
    code_reader = CodeReaderTool()
    content = code_reader.run(file_path)
    return {"code_content": content}

def generate_readme_for_file(file_path: str):
    """
    README oluşturma sürecini yönetir.
    """
    # 1. API Anahtarlarını ve ayarları yükle
    load_dotenv()
    
    print("--- Klaro MVP ---")
    
    # 2. Gerekli bileşenleri hazırla
    # Geri gpt-4o-mini modelini kullanacak şekilde değiştirdim.
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    
    output_parser = StrOutputParser()

    # 3. LangChain Zincirini (Chain) oluştur

    # Yeni bir RunnablePassthrough ile sabit bir 'project_name' değişkeni eklliyoruz.
    # Varsayılan proje adı olarak dosya yolunu kullanıyoruz.
    project_name = os.path.basename(file_path).split('.')[0].replace('_', ' ').title()
    
    # Yeni 'project_info' adımını ekledik.
    project_info = RunnablePassthrough.assign(
        project_name=lambda x: project_name # Dinamik olarak 'main' veya 'prompts' gibi bir isim verecek
    )

    chain = (
        {"file_path": RunnablePassthrough()}
        # 1. Dosya içeriğini oku
        | RunnablePassthrough.assign(code_info=lambda x: get_code_content(x["file_path"]))
        # 2. 'project_name' ve 'code_content' değişkenlerini oluştur ve PromptTemplate'e hazırla
        | {
            "project_name": lambda x: project_name, # Yeni eklenen kısım
            "code_content": lambda x: x["code_info"]["code_content"],
        }
        | README_PROMPT
        | llm
        | output_parser
    )

    print(f"1. Reading and processing '{file_path}'...")
    
    # 4. Zinciri çalıştır ve README'yi oluştur
    try:
        print("2. Generating README.md via LLM (using gpt-4o-mini)...") # Model adını belirttiğimiz bir log ekledim.
        readme_content = chain.invoke(file_path)

        # 5. Sonucu dosyaya kaydet
        generated_filename = "README_generated.md"
        print(f"3. Saving output to '{generated_filename}'...")
        with open(generated_filename, "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        print("\n--- Process Complete ---")
        print(f"Generated README content saved to {generated_filename}")

    except Exception as e:
        print("\n--- AN ERROR OCCURRED ---")
        print(f"An error occurred during the generation process: {e}")
        print("Please check your API keys, network connection, and file paths.")


if __name__ == "__main__":
    # Kullanıcıdan dosya yolunu al
    target_file = input("Enter the path of the Python file to document: ")
    
    # Dosyanın var olup olmadığını kontrol et
    if not os.path.exists(target_file):
        print(f"Error: File not found: {target_file}")
    else:
        generate_readme_for_file(target_file)

