# **Klaro Projesi: Teknik Dokümantasyon Kullanım Kılavuzu**

## **1\. Giriş**

Bu kılavuz, Klaro projesinin geliştirme sürecinde kullanılacak olan temel teknik tasarım belgelerinin amacını, hedef kitlesini ve kullanım senaryolarını açıklamaktadır. Proje ekibinin tutarlı bir vizyonla ilerlemesi ve her geliştiricinin projenin farklı katmanlarını anlaması için bu belgelerin doğru bir şekilde takip edilmesi kritik öneme sahiptir.

Aşağıda listelenen belgeler, projenin genel vizyonundan en derin teknik detaylarına kadar bir bütünlük içinde tasarlanmıştır.

## **2\. Belgeler ve Kullanım Talimatları**

### **Belge 1: Otonom Belgelendirme Ajanı: Proje Planı**

* **Dosya Adı:** klaro\_project\_plan  
* **Amacı:** Projenin "neden" ve "ne" olduğunu açıklayan üst düzey bir belgedir. Projenin iş hedeflerini, vizyonunu, hedef kitlesini ve geliştirme yol haritasını özetler.  
* **Hedef Kitle:** Proje yöneticileri, ürün sahipleri, paydaşlar ve ekibe yeni katılan herkes.  
* **Kullanım Senaryosu:**  
  * **Ekibe Yeni Katılanlar İçin:** Projenin amacını ve hedeflerini anlamak için okunması gereken **ilk belgedir**.  
  * **Yol Haritası Takibi:** Geliştirme aşamalarının (MVP, Aşama 2, vb.) hedeflerini ve zaman çizelgesini takip etmek için kullanılır.  
  * **Sunum ve Raporlama:** Proje hakkında paydaşlara sunum yaparken referans olarak kullanılır.

### **Belge 2: Teknik Tasarım \- Özel Ajan Araçları**

* **Dosya Adı:** tech\_design\_custom\_tools  
* **Amacı:** Ajanın dış dünya ile (kod tabanı) nasıl etkileşim kurduğunu tanımlayan teknik bir belgedir. CodebaseReaderTool ve CodeAnalyzerTool'un mimarisini, fonksiyonlarını ve beklenen çıktılarını detaylandırır.  
* **Hedef Kitle:** Ajanın temel yeteneklerini (kod okuma, analiz etme) geliştirecek olan yazılım mühendisleri.  
* **Kullanım Senaryosu:**  
  * **Geliştirme:** CodebaseReaderTool ve CodeAnalyzerTool sınıflarını kodlarken bu belge bir spesifikasyon olarak kullanılmalıdır.  
  * **Hata Ayıklama (Debugging):** Araçların beklenmedik bir davranış sergilemesi durumunda, beklenen girdi/çıktı formatlarını kontrol etmek için başvurulur.  
  * **Genişletme:** Ajan'a yeni bir "yetenek" (örneğin, bir veritabanı şemasını okuma aracı) eklenmek istendiğinde, mevcut araçların tasarım prensipleri bu belgeden referans alınır.

### **Belge 3: Teknik Tasarım \- Ajan Mimarisi ve Entegrasyonu**

* **Dosya Adı:** tech\_design\_agent\_architecture  
* **Amacı:** Ajanın "beyninin" nasıl çalıştığını açıklar. Araçları nasıl kullanacağına nasıl karar verdiğini (ReAct mimarisi), sistem promptunu ve temel Düşünce \-\> Eylem \-\> Gözlem döngüsünü tanımlar.  
* **Hedef Kitle:** Yapay zeka mühendisleri ve ajanın karar verme mantığı üzerinde çalışan geliştiriciler.  
* **Kullanım Senaryosu:**  
  * **MVP Geliştirme:** Projenin 1\. ve 2\. Aşamalarında, ReAct ajanını kurarken ve ana AgentExecutor'ı oluştururken kullanılır.  
  * **Prompt Mühendisliği:** Ajanın davranışlarını iyileştirmek için sistem promptu üzerinde değişiklikler yaparken bu belgeye başvurulur.  
  * **Akış Analizi:** Ajanın neden belirli bir aracı seçtiğini veya neden bir döngüde takılıp kaldığını anlamak için kullanılır.

### **Belge 4: Teknik Tasarım \- Gelişmiş Ajan Mimarisi (LangGraph)**

* **Dosya Adı:** tech\_design\_advanced\_agent\_langgraph  
* **Amacı:** Projenin gelecekteki, daha sağlam ve hataya dayanıklı versiyonunun planını çizer. ReAct'ten LangGraph'e geçişin nedenlerini ve bu yeni mimarinin (Durum, Düğümler, Kenarlar) nasıl tasarlanacağını anlatır.  
* **Hedef Kitle:** Kıdemli geliştiriciler, sistem mimarları ve projenin uzun vadeli teknik vizyonundan sorumlu olanlar.  
* **Kullanım Senaryosu:**  
  * **Gelecek Planlaması:** Projenin 4\. Aşamasına geçildiğinde, bu belge LangGraph implementasyonu için ana kılavuz olacaktır.  
  * **Karmaşık Senaryolar:** Ajanın hata yönetimi, döngüsel mantık ve daha karmaşık görev akışları gibi yetenekler kazanması gerektiğinde bu tasarıma başvurulur.

## **3\. Önerilen Okuma Sırası**

Bir geliştiricinin projeyi tam olarak anlaması için belgeleri aşağıdaki sırayla okuması tavsiye edilir:

1. **Proje Planı:** "Ne yapıyoruz ve neden?"  
2. **Özel Ajan Araçları:** "Ajanın 'elleri' ve 'gözleri' nasıl çalışıyor?"  
3. **Ajan Mimarisi:** "Ajanın 'beyni' bu 'elleri' ve 'gözleri' nasıl kullanıyor?"  
4. **Gelişmiş Ajan Mimarisi:** "Gelecekte bu 'beyni' nasıl daha akıllı ve sağlam hale getireceğiz?"