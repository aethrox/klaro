# **Otonom Belgelendirme Ajanı: Proje Planı ve Teknik Tasarım**

## **Proje Kimliği: Klaro**

### **İsim: Klaro**

Klaro ismi, Latincede "net", "parlak" ve "aydınlık" anlamına gelen **"clarus"** kelimesinden türetilmiştir. Bu isim, projenin temel misyonunu mükemmel bir şekilde yansıtır: karmaşık ve anlaşılması zor kod tabanlarını aydınlatarak, herkes için net ve anlaşılır belgelere dönüştürmek. Klaro, koda netlik getirir.

### **Slogan**

**Klaro: From Code to Clarity. Instantly.**

## **1\. Projeye Genel Bakış**

### **1.1. Problem**

Yazılım geliştirme süreçlerinde dokümantasyon oluşturmak ve güncel tutmak, kritik öneme sahip olmasına rağmen genellikle zaman alıcı, sıkıcı ve ihmal edilen bir adımdır. Eksik veya güncel olmayan dokümantasyon, yeni ekip üyelerinin projeye adaptasyonunu zorlaştırır, kodun bakımını yavaşlatır ve projenin genel kalitesini düşürür.

### **1.2. Çözüm**

Bu proje, Büyük Dil Modelleri (LLM'ler) ve LangChain ajan mimarisini kullanarak, bir kod tabanını otonom olarak analiz eden ve yüksek kalitede teknik dokümantasyon (README.md, API referansları, geliştirici kılavuzları vb.) üreten bir "Belgelendirme Ajanı" geliştirmeyi amaçlamaktadır. Ajan, minimum geliştirici müdahalesi ile çalışarak dokümantasyon sürecini otomatikleştirecek ve verimliliği artıracaktır.

### **1.3. Hedef Kitle**

* Bireysel yazılım geliştiricileri  
* Yazılım geliştirme ekipleri ve şirketler  
* Açık kaynak proje yöneticileri

### **1.4. Değer Teklifi**

* **Zaman Tasarrufu:** Manuel dokümantasyon yazma süresini %90'a varan oranlarda azaltır.  
* **Kalite ve Tutarlılık:** Proje genelinde profesyonel ve standartlara uygun dokümanlar üretir.  
* **Kolay Bakım:** Kod tabanındaki değişikliklere paralel olarak dokümantasyonun güncellenmesini kolaylaştırır.  
* **Geliştirici Verimliliği:** Geliştiricilerin ana odakları olan kod yazmaya daha fazla zaman ayırmasını sağlar.

## **2\. Teknik Mimari ve Bileşenler**

Ajan, LangChain'in modüler yapısı üzerine inşa edilecek ve aşağıdaki temel bileşenlerden oluşacaktır.

| Bileşen | Teknoloji/LangChain Modülü | Sorumluluk ve İşlev |
| :---- | :---- | :---- |
| **Ajan (Agent)** | langchain.agents (ReAct, etc.) | Projenin beyni. Görevi alt adımlara ayırır, hangi aracı ne zaman kullanacağına karar verir ve genel iş akışını yönetir. |
| **Büyük Dil Modeli (LLM)** | Claude 3.5 Sonnet / GPT-4o | Karmaşık kod yapılarını anlama, akıl yürütme (reasoning), özetleme ve metin üretme gibi temel zeka görevlerini yerine getirir. |
| **Araçlar (Tools)** | langchain.tools (Custom Tools) | Ajanın dış dünya ile etkileşim kurmasını sağlayan yetenek setidir. |
| \* \- CodebaseReaderTool\* | Custom Tool (Python os, git) | Belirtilen bir Git deposunu klonlar veya yerel bir dizindeki tüm ilgili kod dosyalarını (.py, .js, vb.) okur ve içeriğini ajana sunar. |
| \* \- CodeAnalyzerTool\* | Custom Tool (AST, LLM Chain) | Bir kod parçasını (fonksiyon, sınıf) analiz eder; amacını, parametrelerini, geri dönüş değerini ve bağımlılıklarını yapısal olarak çıkarır. |
| \* \- WebSearchTool\* | DuckDuckGo, SerpAPI, etc. | Projenin kullandığı harici kütüphaneler veya framework'ler hakkında bilgi toplamak için web araması yapar. |
| **RAG Mekanizması** | langchain.vectorstores, RetrievalQA | Şirketin mevcut stil kılavuzunu veya benzer projelerdeki dokümantasyon örneklerini referans alarak, üretilen metnin tutarlı ve istenen tonda olmasını sağlar. |
| **Vektör Veritabanı** | ChromaDB / FAISS | RAG için referans dokümanların (stil kılavuzları, örnekler) vektör gömülmelerini (embeddings) depolar ve hızlı anlamsal arama yapılmasını sağlar. |
| **Çıktı Ayrıştırıcı (Output Parser)** | langchain.output\_parsers | LLM tarafından üretilen ham metni, Markdown gibi belirli ve yapısal bir formata (örneğin tam bir README.md dosyası) dönüştürür. |

## **3\. Ajanın İş Akışı (Örnek: README Oluşturma)**

1. **Girdi (Input):** Kullanıcı, ajana bir komut verir: "https://github.com/kullanici/proje-adi adresindeki Python projesi için bir README.md dosyası oluştur."  
2. **Planlama (Reasoning):** Ajan, ana hedefi alt görevlere ayırır:  
   * "İlk olarak, kod tabanına erişmem gerekiyor." \-\> CodebaseReaderTool  
   * "Projenin genel amacını anlamak için ana dosyaları (örn: main.py, app.py) bulup analiz etmeliyim." \-\> CodeAnalyzerTool  
   * "Projenin bağımlılıklarını (requirements.txt) bulup listelemeliyim." \-\> CodebaseReaderTool  
   * "Projenin nasıl kurulacağını ve çalıştırılacağını açıklamalıyım."  
   * "Ana fonksiyonların veya API endpoint'lerinin ne işe yaradığını özetlemeliyim." \-\> CodeAnalyzerTool  
   * "Tüm bu bilgileri birleştirip standart bir README formatında bir taslak oluşturmalıyım."  
   * "Son olarak, taslağı nihai Markdown formatına dönüştürmeliyim." \-\> Output Parser  
3. **Yürütme (Execution):**  
   * Ajan, CodebaseReaderTool'u çağırarak Git deposunu klonlar ve tüm .py dosyalarını okur.  
   * requirements.txt dosyasını okur ve pip install \-r requirements.txt gibi bir kurulum komutu formüle eder.  
   * LLM'in yardımıyla projenin ana giriş noktasını belirler ve CodeAnalyzerTool ile bu dosyadaki ana fonksiyonları veya sınıfları analiz eder.  
   * Her bir ana bileşen için kısa ve anlaşılır açıklamalar üretir.  
   * Eğer boto3 gibi bir kütüphane tespit ederse, WebSearchTool ile bu kütüphanenin ne işe yaradığını araştırarak "AWS ile entegrasyon sağlar" gibi bir not ekleyebilir.  
   * Topladığı tüm bilgileri (proje amacı, kurulum, kullanım, API özeti) bir araya getirir.  
4. **Çıktı (Output):** Ajan, Output Parser kullanarak aşağıdaki gibi formatlanmış, eksiksiz bir README.md dosyası üretir ve kullanıcıya sunar.

## **4\. Geliştirme Yol Haritası**

### **Aşama 1: MVP (Minimum Viable Product) \- (1-2 Hafta)**

* **Hedef:** Tek bir Python betiği için temel bir README.md oluşturan ajan.  
* **Adımlar:**  
  1. LangChain ve LLM (Claude 3.5 Sonnet) entegrasyonunu yap.  
  2. Sadece yerel bir dosyayı okuyan basit bir CodeReaderTool geliştir.  
  3. Dosya içeriğini alıp LLM'e "Bu kod ne yapıyor? Özetle." diyen basit bir zincir (chain) oluştur.  
  4. Çıktıyı Markdown olarak formatlayan bir Output Parser ekle.

### **Aşama 2: Gelişmiş Analiz ve Araç Entegrasyonu \- (2-3 Hafta)**

* **Hedef:** Tüm bir projeyi analiz eden ve daha detaylı doküman üreten ajan.  
* **Adımlar:**  
  1. CodebaseReaderTool'u bir Git deposunu klonlayacak şekilde geliştir.  
  2. Kodun yapısını anlamak için AST (Abstract Syntax Tree) kullanan CodeAnalyzerTool'u oluştur.  
  3. WebSearchTool'u entegre et.  
  4. Ajanın planlama ve akıl yürütme yeteneklerini ReAct (Reasoning and Acting) mantığı ile güçlendir.

### **Aşama 3: RAG ve Kalite Artırımı \- (2 Hafta)**

* **Hedef:** Belirli bir stil kılavuzuna uygun, daha tutarlı dokümanlar üreten ajan.  
* **Adımlar:**  
  1. Örnek dokümanlar ve stil kılavuzları için bir vektör veritabanı (ChromaDB) kur.  
  2. Doküman üretme adımını RAG mekanizması ile zenginleştir.  
  3. Ajanın ürettiği çıktıların kalitesini artırmak için prompt mühendisliği yap.

### **Aşama 4: Stabilizasyon ve LangGraph \- (Opsiyonel, 3+ Hafta)**

* **Hedef:** Hata yönetimi yapabilen, döngüsel ve daha kararlı bir ajan mimarisi.  
* **Adımlar:**  
  1. Mevcut ajan mantığını, durum bilgili (stateful) bir yapı olan LangGraph'a taşı.  
  2. Ajanın hatalı bir adım attığında geri dönüp farklı bir araç denemesini sağlayan döngüler (cycles) ekle.

## **5\. Ticarileştirme Fikirleri**

* **GitHub App:** Projelere PR (Pull Request) ile otomatik olarak dokümantasyon ekleyen bir bot.  
* **SaaS Platformu:** Kullanıcıların Git depolarını bağlayıp anında dokümantasyon alabildikleri bir web uygulaması.  
* **VS Code Eklentisi:** Geliştiricinin doğrudan IDE içerisinden, üzerinde çalıştığı dosya veya fonksiyon için doküman üretmesini sağlayan bir araç.