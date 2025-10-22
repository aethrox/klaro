# **Klaro: Teknik Tasarım \- Gelişmiş Ajan Mimarisi (LangGraph)**

## **1\. Giriş**

Bu belge, Klaro projesinin 4\. Geliştirme Aşamasını detaylandırmaktadır: Mevcut **ReAct** ajan mimarisinden, daha gelişmiş, durum bilgili (stateful) ve esnek bir yapı olan **LangGraph**'e geçiş. Bu yükseltme, ajanın daha karmaşık görevleri yönetme, hatalardan ders çıkarma ve daha sağlam bir karar verme mekanizması oluşturma yeteneğini önemli ölçüde artıracaktır.

## **2\. Neden LangGraph? ReAct Mimarîsinin Sınırları**

ReAct, MVP aşaması için mükemmel bir başlangıç noktası olsa da, doğası gereği durumsuzdur (stateless) ve basit bir Düşünce \-\> Eylem \-\> Gözlem döngüsüne dayanır. Bu durum, aşağıdaki gibi zorluklara yol açabilir:

* **Hata Yönetimi:** Bir araç (tool) başarısız olduğunda veya beklenmedik bir çıktı verdiğinde, ReAct ajanı genellikle döngüyü sonlandırır veya hatayı yönetmekte zorlanır.  
* **Karmaşık Planlama:** Ajanın birden çok adımdan oluşan karmaşık bir planı takip etmesi veya bir adım başarısız olduğunda alternatif bir yola sapması ReAct ile zordur.  
* **Döngüsel Mantık:** "Yeterli bilgi toplayana kadar dosyaları oku" gibi döngüsel mantıklar oluşturmak doğal değildir.

LangGraph, bu sorunları çözmek için bir grafik (graph) veri yapısı sunar. Bu yapı, ajanın mantık akışını düğümler (nodes) ve kenarlar (edges) ile tanımlayarak tam kontrol sağlar.

## **3\. LangGraph Mimarisine Genel Bakış**

LangGraph mimarisi üç ana bileşenden oluşur:

1. **Durum (State):** Grafiğin her adımında taşınan ve güncellenen merkezi bir veri nesnesidir. Ajanın "hafızası" olarak düşünülebilir.  
2. **Düğümler (Nodes):** Belirli bir işi yapan fonksiyonlar veya zincirlerdir (örn: bir aracı çalıştırmak, LLM'e bir soru sormak). Her düğüm, mevcut durumu (state) alır ve güncellenmiş bir durum döndürür.  
3. **Kenarlar (Edges):** Bir düğümden sonra hangi düğümün çalıştırılacağını belirleyen mantıksal bağlantılardır. Bu kenarlar koşullu olabilir, bu da ajanın dinamik kararlar vermesini sağlar.

### **3.1. Klaro Ajanı için Durum (AgentState) Tasarımı**

Klaro ajanının hafızası, aşağıdaki bilgileri içerecek şekilde tasarlanacaktır:

from typing import TypedDict, List, Dict

class AgentState(TypedDict):  
    task: str                 \# Kullanıcının ilk görevi (örn: "README oluştur")  
    file\_tree: str            \# Projenin dosya yapısı  
    files\_read: List\[str\]     \# Okunan dosyaların listesi  
    analysis\_results: Dict    \# CodeAnalyzerTool'dan gelen analiz sonuçları  
    document\_draft: str       \# Geliştirilmekte olan doküman taslağı  
    last\_action\_result: str   \# Son çalıştırılan aracın sonucu  
    error\_log: List\[str\]      \# Karşılaşılan hataların kaydı

### **3.2. Ana Düğümler (Nodes)**

1. **plan\_step (Planlama Düğümü):** Ajanın beyni. Mevcut durumu (AgentState) alır ve bir sonraki adımda hangi aracın hangi parametrelerle çalıştırılacağına karar verir.  
2. **execute\_tool (Araç Yürütme Düğümü):** Planlama düğümünden gelen kararı uygular. Codebase Explorer, File Reader veya Code Analyzer gibi araçlardan birini çalıştırır ve sonucunu last\_action\_result olarak duruma ekler.  
3. **update\_draft (Taslak Güncelleme Düğümü):** execute\_tool'dan gelen yeni bilgileri (dosya içeriği, kod analizi vb.) alır ve document\_draft'ı bu bilgilerle zenginleştirir.  
4. **check\_completeness (Tamamlanma Kontrol Düğümü):** Ajanın görevi tamamlamak için yeterli bilgiye sahip olup olmadığını kontrol eder. Bu düğüm, bir sonraki adımın planlama mı yoksa son çıktıyı oluşturma mı olacağına karar veren koşullu kenarı (conditional edge) tetikler.

## **4\. Örnek İş Akışı Grafiği**

Aşağıda, bir README oluşturma görevi için LangGraph akışının basitleştirilmiş bir diyagramı yer almaktadır:

        \[ Başla \]  
            |  
            v  
    \[ plan\_step \] \--------\> \[ execute\_tool \]  
        ^   |                      |  
        |   |                      v  
        |   '---------------- \[ update\_draft \]  
        |  
        v (Görevi tamamla?)  
\[ check\_completeness \] \--(Hayır)--\> \[ plan\_step \] (Döngü)  
        |  
        '--(Evet)--\> \[ Final Answer \]

### **Koşullu Mantık:**

check\_completeness düğümünden sonraki kenar, ajanın en güçlü özelliğidir.

* **Eğer** LLM, "daha fazla bilgiye ihtiyacım var" derse, kenar akışı tekrar plan\_step düğümüne yönlendirir.  
* **Eğer** LLM, "tüm bilgilere sahibim" derse, kenar akışı Final Answer düğümüne yönlendirerek döngüyü sonlandırır.  
* **Eğer** execute\_tool bir hata döndürürse, durumdaki error\_log güncellenir ve akış yine plan\_step'e döner. Bu sayede ajan, "Bu araç çalışmadı, başka bir şey denemeliyim" diyebilir.

## **5\. Sonuç ve Avantajlar**

LangGraph'e geçiş, Klaro ajanını basit bir araç otomasyonundan, aşağıdaki yeteneklere sahip, sağlam ve akıllı bir sisteme dönüştürecektir:

* **Dayanıklılık (Robustness):** Araç hatalarını yönetebilir ve alternatif yollar deneyebilir.  
* **Gelişmiş Mantık:** Karmaşık, çok adımlı görevleri planlayabilir ve yürütebilir.  
* **Gözlemlenebilirlik:** Graf yapısı sayesinde ajanın karar verme süreci çok daha şeffaf ve kolayca takip edilebilir hale gelir.  
* **Esneklik:** Yeni araçlar veya mantık akışları eklemek, grafiğe yeni düğümler ve kenarlar eklemek kadar kolay olacaktır.