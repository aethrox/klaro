# **Klaro: Teknik Tasarım \- Özel Ajan Araçları**

## **1\. Giriş**

Bu belge, Klaro projesinin otonom belgelendirme ajanının temelini oluşturan özel araçların (Custom Tools) teknik tasarımını açıklamaktadır. Bu araçlar, ajanın bir kod tabanını "görmesini", "gezinmesini" ve "anlamasını" sağlayan temel yeteneklerdir. Tasarımları, ajanın proaktif ve akıllı kararlar alabilmesi için modüler ve ajan odaklı (agentic) bir yaklaşımla yapılmıştır.

## **2\. Temel Tasarım Prensibi: Ajan Odaklı Yetenekler**

Araçlar, tüm kod tabanını tek seferde işleyen monolitik bir yapı yerine, ajanın ihtiyaç duyduğu bilgiyi anlık olarak çekebileceği (pull) bir dizi yetenek olarak tasarlanmıştır. Bu yaklaşım, LLM'lerin bağlam penceresi (context window) limitasyonlarını aşar ve ajanın büyük projelerde bile verimli bir şekilde çalışmasını sağlar. Ajan, direksiyondaki pilot, araçlar ise onun gösterge paneli ve kontrol mekanizmalarıdır.

## **3\. Araç 1: CodebaseReaderTool**

Bu araç, ajanın bir dosya sistemi veya Git deposu ile etkileşim kurmasını sağlar. Temel amacı, ajana keşif ve okuma yetenekleri kazandırmaktır.

### **3.1. Amaç**

Bir Git deposunu veya yerel proje klasörünü analiz ederek, ajanın proje yapısını anlamasını ve belirli dosyaların içeriğine erişmesini sağlamak.

### **3.2. Çözülmesi Gereken Zorluk**

Büyük kod tabanlarının tamamını LLM'in bağlam penceresine sığdırmak imkansızdır. Bu nedenle, ajanın tüm projeyi "görmeden" içinde akıllıca gezinebilmesi gerekir.

### **3.3. Tasarım ve Alt Fonksiyonlar**

CodebaseReaderTool, birden fazla alt fonksiyondan oluşan bir yetenek setidir:

#### **a) list\_files(path: str) \-\> str**

* **Girdi:** Bir Git deposu URL'si veya yerel dosya yolu.  
* **İşlem:**  
  1. Eğer girdi bir URL ise, depoyu geçici bir dizine klonlar.  
  2. Proje kök dizininde gezinerek dosya ve klasör yapısını tarar.  
  3. .gitignore dosyasını okur ve .git, node\_modules, \_\_pycache\_\_ gibi yaygın olarak ihmal edilen dosyalarla birlikte bu listedeki dosyaları filtreler.  
* **Çıktı:** Projenin dosya ağacı yapısını gösteren, temiz ve okunabilir bir metin (string).

#### **b) read\_file(file\_path: str) \-\> str**

* **Girdi:** Okunması istenen dosyanın tam yolu (örneğin, src/main.py).  
* **İşlem:** Belirtilen dosyanın içeriğini okur.  
* **Çıktı:** Dosyanın ham içeriğini içeren bir metin.

### **3.4. Örnek İş Akışı**

1. **Ajan Düşüncesi:** "Projenin genel yapısını anlamam gerekiyor."  
2. **Eylem:** CodebaseReaderTool.list\_files(path="https://github.com/...")  
3. **Gözlem (Araç Çıktısı):**  
   /  
   ├── .gitignore  
   ├── README.md  
   ├── requirements.txt  
   ├── src/  
   │   ├── main.py  
   │   └── utils.py

4. **Ajan Düşüncesi:** "Yapıyı anladım. Bağımlılıkları öğrenmek için requirements.txt dosyasını ve ana mantığı görmek için src/main.py dosyasını okumalıyım."  
5. **Eylem:** CodebaseReaderTool.read\_file(file\_path="requirements.txt")  
6. **Gözlem:** (requirements.txt içeriği)  
7. **Eylem:** CodebaseReaderTool.read\_file(file\_path="src/main.py")  
8. **Gözlem:** (main.py içeriği)

## **4\. Araç 2: CodeAnalyzerTool**

Bu araç, bir kod parçasının "ne yaptığını" anlamsal ve yapısal olarak analiz eder.

### **4.1. Amaç**

Ajan tarafından okunan bir kod dosyasının içeriğini analiz ederek; amacını, içerdiği fonksiyonları, sınıfları ve bunların ilişkilerini yapılandırılmış bir formatta sunmak.

### **4.2. Çözülmesi Gereken Zorluk**

Ham kodu doğrudan LLM'e göndermek, modelin önemli detayları kaçırmasına veya yanlış yorumlamasına (halüsinasyon) neden olabilir. Programatik analiz, bu riski azaltır ve daha güvenilir sonuçlar sağlar.

### **4.3. Tasarım ve Mimari (Hibrit Yaklaşım: AST \+ LLM)**

Bu araç, en iyi sonuçları elde etmek için iki aşamalı bir mimari kullanır:

#### **Aşama 1: Programatik Analiz (AST \- Soyut Sözdizimi Ağacı)**

* Python'un ast kütüphanesi gibi yerleşik araçlar kullanılarak, kodun içeriği programatik olarak ayrıştırılır (parse edilir).  
* Bu aşamada, kodun mantığını anlamadan, aşağıdaki gibi yapısal bilgiler çıkarılır:  
  * Tüm sınıf ve fonksiyon tanımları (ClassDef, FunctionDef).  
  * Fonksiyonların aldığı parametreler, varsayılan değerleri ve tip ipuçları (type hints).  
  * Mevcut docstring'ler.

#### **Aşama 2: Anlamsal Özetleme (LLM)**

* AST aşamasında çıkarılan yapısal veriler, LLM'e özel bir prompt şablonu ile gönderilir.  
* Bu prompt, LLM'den bu yapısal bilgileri ve docstring'leri kullanarak her bir bileşenin (fonksiyon/sınıf) amacını "insan dilinde" açıklamasını ve dosyanın genel bir özetini çıkarmasını ister.

### **4.4. Girdi ve Çıktı Formatı**

* **Girdi:** Analiz edilecek kod içeriğini içeren bir metin (string).  
* **Çıktı:** Ajanın kolayca işleyebileceği, standart bir JSON nesnesi.

**Örnek JSON Çıktısı:**

{  
  "file\_path": "src/utils.py",  
  "summary": "Bu modül, kullanıcı verilerini işlemek ve doğrulamak için yardımcı fonksiyonlar içerir.",  
  "components": \[  
    {  
      "type": "function",  
      "name": "format\_user\_data",  
      "parameters": \["user\_id (int)", "data (dict)"\],  
      "returns": "dict",  
      "description": "Kullanıcı verisini alır ve API için standart bir formata dönüştürür."  
    },  
    {  
      "type": "function",  
      "name": "validate\_email",  
      "parameters": \["email (str)"\],  
      "returns": "bool",  
      "description": "Verilen e-postanın geçerli bir formatta olup olmadığını kontrol eder."  
    }  
  \]  
}

## **5\. Sonraki Adımlar**

Bu iki temel araç, projenin temelini oluşturmaktadır. Bir sonraki teknik aşama, bu araçları bir LangChain Ajanı (örneğin, ReAct Agent) ile entegre ederek, ajanın bu yetenekleri kullanarak otonom bir şekilde planlama yapmasını ve görevleri yürütmesini sağlamaktır.