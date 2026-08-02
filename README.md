# Markdown Merge

Large Markdown collections için geliştirilmiş, token sınırına duyarlı ve üretim kullanıma hazır bir Python aracıdır.

Markdown Merge; kaynak dosyaları yalnızca art arda eklemek yerine içerikleri temizler, kaynak sınırlarını korur, otomatik içindekiler bölümü oluşturur, `tiktoken` ile gerçek token sayımı yapar ve belirlenen sınırı aşmayan çıktı parçaları üretir.

Proje; yapay zeka dokümantasyon hazırlığı, RAG sistemleri, semantik arama, embedding üretimi ve büyük bilgi tabanlarının düzenlenmesi için tasarlanmıştır.

---

## Özellikler

- Yalnızca Python ile geliştirilmiştir.
- `.md` ve `.markdown` dosyalarını destekler.
- Kaynak klasörü ve tüm alt klasörleri tarar.
- Markdown dışındaki dosyaları yok sayar.
- Gereksiz boş satırları temizler.
- Bozuk ve gereksiz HTML parçalarını temizler.
- Uzun Base64 görsel verilerini kaldırır.
- Her kaynak dosyanın önüne kaynak etiketi ekler.
- Her çıktı parçası için otomatik içindekiler bölümü üretir.
- OpenAI `tiktoken` kütüphanesiyle gerçek token sayımı yapar.
- Varsayılan olarak her çıktı dosyasını en fazla 80.000 token ile sınırlar.
- Büyük kaynak belgeleri güvenli Markdown sınırlarından böler.
- Dosyaları atomik biçimde yazar.
- Her çıktı için SHA-256 özeti üretir.
- Kaynak ve çıktı eşleşmelerini JSON manifest dosyasına kaydeder.
- Her çalıştırma için zaman damgalı log dosyası oluşturur.
- Rich tabanlı terminal arayüzü ve çalışma istatistikleri sunar.
- İçeriğe göre genel ve akıllı çıktı adı üretir.
- Ruff, MyPy, Pytest ve coverage kontrollerini destekler.
- Terminalin herhangi bir konumundan `mdmerge` komutuyla çalışır.

---

## Akıllı Çıktı İsimlendirme

Özel bir çıktı adı verilmediğinde proje Markdown koleksiyonunu otomatik analiz eder.

Analiz sırasında şunlar değerlendirilir:

- kaynak klasörün anlamlı adı
- Markdown belge başlıkları
- tekrar eden başlık ifadeleri
- koleksiyon içinde tekrar eden anlamlı terimler

Örnek otomatik çıktı adları:

    Instagram_Help_Center_Part_01_of_16.md
    Acme_API_Reference_Part_01_of_04.md
    Product_User_Guide_Part_01_of_03.md
    Merged_Markdown_Part_01_of_02.md

İsimlendirme herhangi bir siteye veya markaya özel değildir. Her çalıştırmada verilen Markdown koleksiyonu yeniden analiz edilir.

İstenirse otomatik isimlendirme geçersiz kılınabilir:

    mdmerge INPUT_DIRECTORY OUTPUT_DIRECTORY --output-prefix Custom_Name

---

## Gereksinimler

- Python 3.13 veya üzeri
- uv
- tiktoken

---

## Kurulum

Depoyu klonlayın:

    git clone https://github.com/YOUR_USERNAME/markdownMerge.git
    cd markdownMerge

Proje ortamını ve tüm bağımlılıkları kurun:

    uv sync --all-groups

Global terminal komutunu kurun:

    uv tool install --editable . --force

Global komutun çalıştığını doğrulayın:

    mdmerge --version
    mdmerge --help

---

## Kullanım

Temel kullanım:

    mdmerge INPUT_DIRECTORY OUTPUT_DIRECTORY

Örnek:

    mdmerge "/mnt/local/areas/source-docs" "/mnt/local/areas/merged-docs"

Proje içinden doğrudan Python ile çalıştırma:

    uv run python main.py INPUT_DIRECTORY OUTPUT_DIRECTORY

Örnek:

    uv run python main.py \
      "/mnt/local/areas/source-docs" \
      "/mnt/local/areas/merged-docs"

---

## Komut Seçenekleri

Yardım ekranını açmak için:

    mdmerge --help

Desteklenen seçenekler:

    --token-limit INTEGER
    --encoding TEXT
    --output-prefix TEXT
    --toc-reserve INTEGER
    --version
    --help

Özel token sınırıyla çalıştırma:

    mdmerge \
      "/mnt/local/areas/source-docs" \
      "/mnt/local/areas/merged-docs" \
      --token-limit 80000

Özel çıktı adıyla çalıştırma:

    mdmerge \
      "/mnt/local/areas/source-docs" \
      "/mnt/local/areas/merged-docs" \
      --output-prefix Product_Knowledge_Base

---

## Kaynak Tarama Davranışı

Verilen giriş klasörünün tamamı özyinelemeli olarak taranır.

Örnek kaynak yapısı:

    source-docs/
    ├── README.md
    ├── guides/
    │   ├── installation.md
    │   └── configuration.md
    ├── api/
    │   └── reference.markdown
    └── images/
        └── screenshot.png

Bu yapıda yalnızca aşağıdaki dosyalar işlenir:

    README.md
    guides/installation.md
    guides/configuration.md
    api/reference.markdown

`screenshot.png` ve diğer Markdown dışı dosyalar birleştirmeye dahil edilmez.

---

## Çıktı Yapısı

Örnek çıktı klasörü:

    merged-docs/
    ├── Product_User_Guide_Part_01_of_03.md
    ├── Product_User_Guide_Part_02_of_03.md
    ├── Product_User_Guide_Part_03_of_03.md
    └── merge_manifest.json

Her Markdown çıktı parçası şunları içerir:

- üretim zamanı
- kullanılan token encoding bilgisi
- maksimum token sınırı
- kaynak belge sayısı
- kaynak segment sayısı
- içindekiler bölümü
- açık kaynak başlıkları
- temizlenmiş Markdown içerikleri

Kaynak bölümü örneği:

    ---

    ## Source: `guides/installation.md`

    <!-- source-path: guides/installation.md -->
    <!-- source-segment: 1/1 -->

    # Installation

    Document content...

---

## Token Bölme Sistemi

Varsayılan token sınırı:

    80000

Varsayılan encoding:

    o200k_base

Proje karakter veya kelime sayısına göre yaklaşık hesap yapmaz. Metni doğrudan `tiktoken` ile encode eder ve gerçek token sayısını kullanır.

Bir kaynak belge tek başına sınırı aşıyorsa güvenli parçalara ayrılır. Son çıktı oluşturulduktan sonra token sayısı tekrar doğrulanır ve sınırı aşan dosyanın yazılmasına izin verilmez.

---

## Manifest

Her çalıştırmada aşağıdaki dosya oluşturulur:

    merge_manifest.json

Manifest şunları içerir:

- giriş klasörü
- çıktı klasörü
- token encoding
- token sınırı
- çalışma istatistikleri
- çıktı dosyalarının adları
- her parçanın token sayısı
- karakter sayıları
- SHA-256 özetleri
- kaynak dosya ve segment eşleşmeleri
- uyarılar

---

## Log Sistemi

Her çalışma için ayrı bir zaman damgalı log oluşturulur:

    logs/markdown_merge_YYYY-MM-DD_HH-MM-SS_microseconds.log

Kalite kontrolleri için de ayrı log oluşturulur:

    logs/quality_YYYY-MM-DD_HH-MM-SS.log

Log dosyaları çalışma başlangıcını, işlenen kaynakları, bölme işlemlerini, oluşturulan çıktıları, token sayılarını, hataları ve çalışma süresini içerir.

---

## Kalite Kontrolleri

Tüm kalite kontrollerini tek komutla çalıştırın:

    ./quality.sh

Bu komut aşağıdaki kontrolleri uygular:

- Ruff format doğrulaması
- Ruff lint doğrulaması
- MyPy strict tip kontrolü
- Pytest test paketi
- Coverage kontrolü
- Global CLI yardım testi
- Doğrudan Python giriş noktası testi

Kontrolleri ayrı ayrı çalıştırmak için:

    uv run ruff format --check .
    uv run ruff check .
    uv run mypy
    uv run pytest

---

## Test Durumu

Proje aşağıdaki alanlar için otomatik testler içerir:

- Markdown temizleme
- Base64 görsel verisi kaldırma
- özyinelemeli dosya keşfi
- Markdown dışı dosyaları dışlama
- içerik tabanlı akıllı isimlendirme
- TOC ve kaynak başlığı oluşturma
- token sınırına göre kaynak bölme
- uçtan uca merge işlemi
- manifest oluşturma
- çıktı token doğrulaması

---

## Proje Yapısı

    markdownMerge/
    ├── main.py
    ├── pyproject.toml
    ├── quality.sh
    ├── README.md
    ├── src/
    │   └── markdown_merge/
    │       ├── __init__.py
    │       ├── cleaner.py
    │       ├── cli.py
    │       ├── config.py
    │       ├── discovery.py
    │       ├── logging_setup.py
    │       ├── models.py
    │       ├── naming.py
    │       ├── packer.py
    │       ├── reader.py
    │       ├── renderer.py
    │       ├── service.py
    │       ├── splitter.py
    │       ├── tokenizer.py
    │       ├── ui.py
    │       └── writer.py
    └── tests/

---

## Kullanım Alanları

- büyük dokümantasyon koleksiyonları
- yapay zeka dosya hazırlığı
- RAG veri kaynakları
- semantik arama
- embedding üretimi
- bilgi tabanı birleştirme
- teknik dokümantasyon arşivleme
- LLM bağlam dosyaları
- File Search sistemleri

---

## Lisans

MIT License.
