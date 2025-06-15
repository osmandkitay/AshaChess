1. Kuralların Tanımı ve Formalizasyonu
Açık, matematiksel tanım

Her yeni kural için girdi (pozisyon şartı), işlem (hamle dönüşümü), çıktı (yeni pozisyon ve durum güncellemesi) üçlüsünü netleştir.

Örnek üzerinden senaryolar

En basitinden en karmaşığına birkaç örnek pozisyon çiz (FEN, UCI vb.) ve beklenen çıktı hamlelerini not et.

2. Durum Temsili (Game State)
Board veri yapısı

Eğer chess.Board gibi hazır bir obje kullanıyorsan, içine ek bayraklar (flag) ekle:

Örn. super_pawn_eligible, variable_castling_rights vb.

FEN uzantısı

Kendi FEN/PGN formatında yeni bayrakları nasıl taşıyacağını belirle.

3. Hamle Üretimi (Move Generator)
Yeni kural koşulları

Hamle ağacı (move tree) üretirken, öncelikle mevcut hamle jeneratörünü genişlet:

Standart hamleler

Yeni kural hamleleri (önceliklendirme, özel filtre)

UCI/UCCI desteği

Eğer engine ile haberleşiyorsan, yeni hamle tipleri için UCI çıktısını da güncelle.

4. Legal Move Checker
Geçerlilik kontrolü

En önemli nokta “hamle geçerli mi?” sorusunu, yeni kuralı da göz önüne alarak yanıtlamak.

Örn. “King’s Step” kuralı için:

Şah kontrol altında mı?

İki kare gidiyorsa ara kare de kontrol altında olmamalı.

Test matrisleri

Tüm kenar durumlarını (edge cases) bir matris hâlinde listele ve otomatik test yaz.

5. Oyun Durumu Güncellemesi & UI
Backend ↔ Frontend uyumu

Hamle yapıldığında oyun durumuna ek bilgiler geliyorsa (örneğin ek bayraklar), UI’da da

Geçerli kare vurgulamaları

Terfi seçenekleri

Rok için ekstra butonlar
bunları ekle.

Event Listener yönetimi

initializeBoard’da eskileri temizleyip yalnızca bir set ekle (örn. removeEventListener veya tek seferlik callback).

6. Değerlendirme (Evaluation) Fonksiyonu
Eğer bir AI rakip varsa, yeni kuralın pozisyon değerlendirmenin (material + positional) parçası olması gerekir.

Örneğin “süper piyon” +1.5 değer kazandırıyorsa, statik değerlendirme matrisine yansıt.

7. Test ve Doğrulama
Birim testleri (Unit tests)

Her yeni hamle tipi için assert’lerle pozisyon girdi–çıktı testleri yaz.

Entegrasyon testleri

Oyun akışı içinde “yeni kuralı kullanma, geri alma, tekrar oynama” senaryoları.

Simülasyon / Self-play

Otomatik yüzlerce pozisyonda rule-in ve rule-out testleri.

8. Performans & Optimizasyon
Yeni kural dallanma sayısını (branching factor) nasıl etkiliyor?

Alpha-Beta’nın budama etkinliği hâlâ yeterli mi?

Gerekirse move ordering politikasına kural önceliği ekle.

9. Geriye Dönük Uyumluluk
Eski FIDE/FEN pozisyonları hâlâ aynı sonucu vermeli.

Yeni bayrak taşıyan pozisyonları eski sürüm nasıl yorumlardı? (Örn. terfi bayrağı yoksayılır.)