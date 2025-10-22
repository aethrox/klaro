# **Klaro: Teknik Tasarım \- Ajan Mimarisi ve Entegrasyonu**

## **1\. Giriş**

Bu belge, tech\_design\_custom\_tools dosyasında tasarlanan özel araçları (CodebaseReaderTool, CodeAnalyzerTool) kullanacak olan otonom ajanın mimarisini, entegrasyonunu ve temel çalışma prensiplerini açıklamaktadır. Bu aşama, projenin "beynini" oluşturarak, ajanın otonom bir şekilde görevleri planlamasını ve yürütmesini sağlar.

## **2\. Ajan Mimarisi Seçimi: ReAct (Reasoning and Acting)**

Projenin ilk ve MVP (Minimum Viable Product) aşamaları için LangChain'in **ReAct** ajan mimarisi kullanılacaktır.

### **2.1. Neden ReAct?**

* **Basitlik ve Anlaşılabilirlik:** ReAct, Düşünce \-\> Eylem \-\> Gözlem (Thought \-\> Action \-\> Observation) döngüsü ile çalışır. Bu yapı, ajanın karar verme sürecini takip etmeyi ve hata ayıklamayı (debugging) son derece kolaylaştırır.  
* **Etkin Araç Kullanımı:** Bu mimari, LLM'in hangi aracı neden seçtiğini ve bir sonraki adımda ne yapmayı planladığını açıkça belirtmesini gerektirir. Bu, araç odaklı görevler için idealdir.  
* **Endüstri Standardı:** LangChain'deki en yaygın ve iyi belgelendirilmiş ajan türlerinden biridir, bu da hızlı bir başlangıç yapmayı sağlar.

## **3\. Ajan ve Araçların Entegrasyonu**

Ajanın tasarlanan özel araçları kullanabilmesi için bu araçların LangChain formatında tanımlanması ve ajana "sunulması" gerekir.

### **3.1. Araçların Tanımlanması**

Her özel araç, bir Tool nesnesi olarak paketlenmelidir. Bu nesne en az iki önemli parametre içerir:

* **name:** LLM'in aracı çağırmak için kullanacağı benzersiz isim (örn: codebase\_reader veya code\_analyzer).  
* **description:** **En kritik bölüm.** LLM'in bu aracın ne işe yaradığını, hangi durumlarda kullanılması gerektiğini ve hangi parametreleri aldığını anladığı yer burasıdır. Açıklama ne kadar net olursa, ajan o kadar akıllı olur.

**Örnek Araç Tanımlaması (Python Kodu Konsepti):**

from langchain.agents import Tool  
from your\_tools import CodebaseReaderTool, CodeAnalyzerTool

\# Araç nesnelerini oluştur  
reader\_tool \= CodebaseReaderTool()  
analyzer\_tool \= CodeAnalyzerTool()

tools \= \[  
    Tool(  
        name="Codebase Explorer",  
        func=reader\_tool.list\_files,  
        description="Bir Git deposunun veya yerel klasörün dosya yapısını listelemek için kullanılır. Projeye başlarken ilk olarak bu aracı kullanmalısın."  
    ),  
    Tool(  
        name="File Reader",  
        func=reader\_tool.read\_file,  
        description="Belirli bir dosyanın içeriğini okumak için kullanılır. Argüman olarak dosya yolunu (file\_path) almalıdır."  
    ),  
    Tool(  
        name="Code Analyzer",  
        func=analyzer\_tool.analyze,  
        description="Bir kod dosyasının içeriğini analiz etmek, özetlemek ve içindeki fonksiyon/sınıfları yapısal olarak çıkarmak için kullanılır."  
    )  
\]

### **3.2. Ajan Yürütücüsünün (Agent Executor) Oluşturulması**

Tanımlanan araçlar, LLM ve bir ana prompt ile birlikte bir AgentExecutor içinde birleştirilir. Bu yürütücü, tüm Düşünce \-\> Eylem \-\> Gözlem döngüsünü yönetir.

## **4\. Sistem/Ana Prompt Tasarımı**

Ajanın davranışını şekillendiren en önemli unsurlardan biri, ona verilen ilk talimatlardır (sistem promptu). Bu prompt, ajanın kimliğini, görevini, kurallarını ve araçlarını nasıl kullanacağını tanımlar.

**Örnek Sistem Promptu:**

Sen, Klaro adında uzman bir yapay zeka asistanısın. Görevin, sana verilen bir kod tabanını analiz ederek otonom bir şekilde yüksek kalitede, net ve profesyonel teknik dokümantasyon (README.md dosyası) oluşturmaktır.

Sana verilen görevleri yerine getirmek için aşağıdaki araçlara erişimin var:

1\.  \*\*Codebase Explorer:\*\* Bir projenin dosya yapısını listeler. Analize her zaman bu araçla başla.  
2\.  \*\*File Reader:\*\* Belirli bir dosyanın içeriğini okur.  
3\.  \*\*Code Analyzer:\*\* Bir kod parçasının amacını ve yapısını analiz eder.

\*\*Kuralların:\*\*  
\- Adım adım düşünmelisin. Her adımda ne yapacağını ve neden yapacağını açıkla.  
\- Her zaman proje yapısını listeleyerek başla.  
\- Projenin amacını, bağımlılıklarını, nasıl kurulacağını ve nasıl kullanılacağını belirle.  
\- Önemli fonksiyonları veya sınıfları analiz ederek dokümantasyonun "Kullanım" veya "API" bölümünü oluştur.  
\- Tüm bilgileri topladıktan sonra, "Final Answer" olarak tam ve formatlanmış bir Markdown çıktısı sun.

## **5\. Örnek Çalışma Döngüsü: Adım Adım README Oluşturma**

Aşağıda, ajanın yukarıdaki prompt ve araçlarla bir görevi nasıl tamamladığının basitleştirilmiş bir simülasyonu yer almaktadır:

**Kullanıcı Girdisi:** "https://github.com/kullanici/proje-adi" için bir README oluştur.

**Döngü 1:**

* **Düşünce:** Kullanıcı bir README dosyası istedi. Görevime başlamak için önce projenin dosya yapısını anlamalıyım. Bunun için Codebase Explorer aracını kullanacağım.  
* **Eylem:** Codebase Explorer(path="https://github.com/kullanici/proje-adi")  
* **Gözlem:**  
  /  
  ├── requirements.txt  
  ├── src/  
  │   ├── main.py

**Döngü 2:**

* **Düşünce:** Proje yapısını gördüm. requirements.txt dosyası bağımlılıkları içeriyor olmalı. src/main.py ise ana kod gibi duruyor. Önce bağımlılıkları öğrenmek için File Reader ile requirements.txt dosyasını okuyacağım.  
* **Eylem:** File Reader(file\_path="requirements.txt")  
* **Gözlem:** fastapi\\nuvicorn

**Döngü 3:**

* **Düşünce:** Tamam, bu bir FastAPI projesi. Şimdi ana mantığı anlamak için src/main.py dosyasını okumalıyım.  
* **Eylem:** File Reader(file\_path="src/main.py")  
* **Gözlem:** (main.py'nin içeriği)

**Döngü 4:**

* **Düşünce:** main.py içeriğini aldım. Şimdi bu kodun ne yaptığını, hangi API endpoint'lerine sahip olduğunu anlamak için Code Analyzer aracını kullanmalıyım.  
* **Eylem:** Code Analyzer(code\_content="...")  
* **Gözlem:** (CodeAnalyzerTool'dan gelen JSON çıktısı)

**... (Ajan yeterli bilgi toplayana kadar bu döngü devam eder) ...**

**Son Adım:**

* **Düşünce:** Projenin amacını (FastAPI), bağımlılıklarını, kurulum adımlarını (pip install) ve API endpoint'lerini öğrendim. Artık son README dosyasını oluşturmak için yeterli bilgiye sahibim.  
* **Final Answer:**  
  \# Proje Adı

  Bu proje, FastAPI kullanılarak oluşturulmuş bir web servisidir.

  \#\# Kurulum

  ...

  \#\# API Endpoints

  ...

## **6\. Gelecek Adım: LangGraph'e Geçiş**

ReAct mimarisi MVP için yeterli olsa da, daha karmaşık projelerde veya ajanın hatalarla karşılaştığı durumlarda yetersiz kalabilir. Projenin 4\. Aşamasında, daha esnek, durum bilgili (stateful) ve döngüsel (cyclical) mantık akışları oluşturmaya olanak tanıyan **LangGraph**'e geçiş yapılması planlanmaktadır. Bu, ajanın daha sağlam ve hataya dayanıklı olmasını sağlayacaktır.