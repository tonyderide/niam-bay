/* =====================================================================
   Nihongo — Données (kana + vocabulaire)
   ---------------------------------------------------------------------
   Kana : { k: caractère, r: romaji, m: mnémonique (fr), g: groupe }
   Vocab: { jp, kana, romaji, fr, theme, ex: { jp, fr } }
   ===================================================================== */

/* ---------- HIRAGANA de base (gojūon) avec mnémoniques ---------- */
const HIRA_BASE = [
  { k: "あ", r: "a",  m: "Un « A » avec une pomme (Apple) accrochée." },
  { k: "い", r: "i",  m: "Deux barres comme deux anguilles (eels = « i »)." },
  { k: "う", r: "u",  m: "Un visage de profil qui dit « ouh »." },
  { k: "え", r: "e",  m: "Une autruche exotique (« e ») qui tend le cou." },
  { k: "お", r: "o",  m: "Un « o » avec une queue, comme une grosse olive." },
  { k: "か", r: "ka", m: "Un couteau (Katana) qui coupe : ka !" },
  { k: "き", r: "ki", m: "Une clé (Key) suspendue." },
  { k: "く", r: "ku", m: "Le bec d'un coucou : « ku ku »." },
  { k: "け", r: "ke", m: "Un sac de Ketchup renversé." },
  { k: "こ", r: "ko", m: "Deux vers de terre (« co » comme cocon)." },
  { k: "さ", r: "sa", m: "Un poisson (saumon = sa) qui nage." },
  { k: "し", r: "shi", m: "Un hameçon : on pêche, « shhh »." },
  { k: "す", r: "su", m: "Une boucle, comme un swing de balançoire." },
  { k: "せ", r: "se", m: "Une bouche qui dit « say » (se)." },
  { k: "そ", r: "so", m: "Du fil de couture (so = sew) en zigzag." },
  { k: "た", r: "ta", m: "Un « t » et un « a » collés : ta." },
  { k: "ち", r: "chi", m: "Une joue (cheek) ronde : chi." },
  { k: "つ", r: "tsu", m: "Une vague tsunami : tsu." },
  { k: "て", r: "te", m: "Une table (te) vue de côté." },
  { k: "と", r: "to", m: "Un orteil (toe) avec un clou planté." },
  { k: "な", r: "na", m: "Un genou (knee → na) plié avec une croix." },
  { k: "に", r: "ni", m: "Un genou (knee) et une aiguille : ni." },
  { k: "ぬ", r: "nu", m: "Des nouilles (noodles = nu) emmêlées." },
  { k: "ね", r: "ne", m: "Un chat qui fait « nya » avec sa queue enroulée." },
  { k: "の", r: "no", m: "Un panneau d'interdiction : NO." },
  { k: "は", r: "ha", m: "Un « h » et un « a » : ha ha, on rit." },
  { k: "ひ", r: "hi", m: "Une bouche qui sourit, dit « hiii »." },
  { k: "ふ", r: "fu", m: "Le mont Fuji esquissé : fu." },
  { k: "へ", r: "he", m: "Une colline : on grimpe en disant « hey » (he)." },
  { k: "ほ", r: "ho", m: "Comme は (ha) mais avec une barre : Ho ho ho !" },
  { k: "ま", r: "ma", m: "Maman (ma) avec deux boucles dans les cheveux." },
  { k: "み", r: "mi", m: "Le chiffre 21 retourné… « mi » comme 3 (mittsu)." },
  { k: "む", r: "mu", m: "Une vache (« meuh » → mu) avec une queue." },
  { k: "め", r: "me", m: "Un œil (« me » regarde-moi)." },
  { k: "も", r: "mo", m: "Un hameçon avec deux appâts : « more » (mo)." },
  { k: "や", r: "ya", m: "Un yak (ya) avec des cornes." },
  { k: "ゆ", r: "yu", m: "Un poisson unique (unique = yu)." },
  { k: "よ", r: "yo", m: "Un yo-yo qui pend." },
  { k: "ら", r: "ra", m: "Un lapin (rabbit) qui saute : ra." },
  { k: "り", r: "ri", m: "Une rivière (river = ri) à deux courants." },
  { k: "る", r: "ru", m: "Une boucle de route (route = ru)." },
  { k: "れ", r: "re", m: "Comme る mais une jambe tendue : « re »." },
  { k: "ろ", r: "ro", m: "Une route (road = ro) carrée sans boucle." },
  { k: "わ", r: "wa", m: "Comme れ mais arrondi : « wa » (waouh)." },
  { k: "を", r: "wo", m: "Une bouche qui lance : « wo ! » (particule o)." },
  { k: "ん", r: "n",  m: "Un « n » bouclé, le seul son consonne seul." },
];

/* ---------- HIRAGANA dakuten / handakuten ---------- */
const HIRA_DAKUTEN = [
  { k: "が", r: "ga" }, { k: "ぎ", r: "gi" }, { k: "ぐ", r: "gu" }, { k: "げ", r: "ge" }, { k: "ご", r: "go" },
  { k: "ざ", r: "za" }, { k: "じ", r: "ji" }, { k: "ず", r: "zu" }, { k: "ぜ", r: "ze" }, { k: "ぞ", r: "zo" },
  { k: "だ", r: "da" }, { k: "ぢ", r: "ji" }, { k: "づ", r: "zu" }, { k: "で", r: "de" }, { k: "ど", r: "do" },
  { k: "ば", r: "ba" }, { k: "び", r: "bi" }, { k: "ぶ", r: "bu" }, { k: "べ", r: "be" }, { k: "ぼ", r: "bo" },
  { k: "ぱ", r: "pa" }, { k: "ぴ", r: "pi" }, { k: "ぷ", r: "pu" }, { k: "ぺ", r: "pe" }, { k: "ぽ", r: "po" },
];

/* ---------- HIRAGANA yōon (combinaisons) ---------- */
const HIRA_YOON = [
  { k: "きゃ", r: "kya" }, { k: "きゅ", r: "kyu" }, { k: "きょ", r: "kyo" },
  { k: "しゃ", r: "sha" }, { k: "しゅ", r: "shu" }, { k: "しょ", r: "sho" },
  { k: "ちゃ", r: "cha" }, { k: "ちゅ", r: "chu" }, { k: "ちょ", r: "cho" },
  { k: "にゃ", r: "nya" }, { k: "にゅ", r: "nyu" }, { k: "にょ", r: "nyo" },
  { k: "ひゃ", r: "hya" }, { k: "ひゅ", r: "hyu" }, { k: "ひょ", r: "hyo" },
  { k: "みゃ", r: "mya" }, { k: "みゅ", r: "myu" }, { k: "みょ", r: "myo" },
  { k: "りゃ", r: "rya" }, { k: "りゅ", r: "ryu" }, { k: "りょ", r: "ryo" },
  { k: "ぎゃ", r: "gya" }, { k: "ぎゅ", r: "gyu" }, { k: "ぎょ", r: "gyo" },
  { k: "じゃ", r: "ja" },  { k: "じゅ", r: "ju" },  { k: "じょ", r: "jo" },
  { k: "びゃ", r: "bya" }, { k: "びゅ", r: "byu" }, { k: "びょ", r: "byo" },
  { k: "ぴゃ", r: "pya" }, { k: "ぴゅ", r: "pyu" }, { k: "ぴょ", r: "pyo" },
];

/* ---------- KATAKANA de base ---------- */
const KATA_BASE = [
  { k: "ア", r: "a",  m: "Un « A » anguleux, comme un toit." },
  { k: "イ", r: "i",  m: "Deux traits, une aiguille (« i »)." },
  { k: "ウ", r: "u",  m: "Un toit avec un petit trait." },
  { k: "エ", r: "e",  m: "Un escalier (« e »)." },
  { k: "オ", r: "o",  m: "Un « o » avec une croix." },
  { k: "カ", r: "ka", m: "Comme か mais raide : ka." },
  { k: "キ", r: "ki", m: "Une clé (key) anguleuse." },
  { k: "ク", r: "ku", m: "Un bec ouvert : ku." },
  { k: "ケ", r: "ke", m: "Trois traits : Ketchup." },
  { k: "コ", r: "ko", m: "Un coin (corner) : ko." },
  { k: "サ", r: "sa", m: "Trois traits, comme un soleil." },
  { k: "シ", r: "shi", m: "Deux points qui montent : shi (≠ ツ)." },
  { k: "ス", r: "su", m: "Une boucle vers le bas." },
  { k: "セ", r: "se", m: "Comme せ en plus carré." },
  { k: "ソ", r: "so", m: "Deux traits qui descendent : so (≠ ン)." },
  { k: "タ", r: "ta", m: "Un « ta » qui ressemble à un parapluie." },
  { k: "チ", r: "chi", m: "Un « + » avec un chapeau : chi." },
  { k: "ツ", r: "tsu", m: "Trois traits horizontaux : tsu (≠ シ)." },
  { k: "テ", r: "te", m: "Une table avec une jambe." },
  { k: "ト", r: "to", m: "Un « T » avec un orteil (toe)." },
  { k: "ナ", r: "na", m: "Une croix penchée : na." },
  { k: "ニ", r: "ni", m: "Deux traits = ni (2 = ni en japonais !)." },
  { k: "ヌ", r: "nu", m: "Comme ス avec un trait en plus." },
  { k: "ネ", r: "ne", m: "Un caractère touffu : ne." },
  { k: "ノ", r: "no", m: "Un seul trait : NO." },
  { k: "ハ", r: "ha", m: "Deux jambes écartées : ha." },
  { k: "ヒ", r: "hi", m: "Un talon de chaussure : hi." },
  { k: "フ", r: "fu", m: "Un nez qui souffle : fu." },
  { k: "ヘ", r: "he", m: "Identique à へ : une colline." },
  { k: "ホ", r: "ho", m: "Une croix avec deux pieds : ho." },
  { k: "マ", r: "ma", m: "Un drapeau : ma." },
  { k: "ミ", r: "mi", m: "Trois traits : mi (3 = mi)." },
  { k: "ム", r: "mu", m: "Une bouche de vache : mu (meuh)." },
  { k: "メ", r: "me", m: "Un « X » : me (un œil croisé)." },
  { k: "モ", r: "mo", m: "Un hameçon avec deux barres." },
  { k: "ヤ", r: "ya", m: "Un boomerang : ya." },
  { k: "ユ", r: "yu", m: "Un « U » carré couché." },
  { k: "ヨ", r: "yo", m: "Un « E » à l'envers : yo." },
  { k: "ラ", r: "ra", m: "Un toit avec un trait : ra." },
  { k: "リ", r: "ri", m: "Deux traits verticaux : ri (comme り)." },
  { k: "ル", r: "ru", m: "Deux jambes qui courent (route)." },
  { k: "レ", r: "re", m: "Un coche : re." },
  { k: "ロ", r: "ro", m: "Un carré : road (ro)." },
  { k: "ワ", r: "wa", m: "Comme ロ mais ouvert : wa." },
  { k: "ヲ", r: "wo", m: "Rare : la particule o en katakana." },
  { k: "ン", r: "n",  m: "Deux traits qui montent : n (≠ ソ)." },
];

const KATA_DAKUTEN = [
  { k: "ガ", r: "ga" }, { k: "ギ", r: "gi" }, { k: "グ", r: "gu" }, { k: "ゲ", r: "ge" }, { k: "ゴ", r: "go" },
  { k: "ザ", r: "za" }, { k: "ジ", r: "ji" }, { k: "ズ", r: "zu" }, { k: "ゼ", r: "ze" }, { k: "ゾ", r: "zo" },
  { k: "ダ", r: "da" }, { k: "ヂ", r: "ji" }, { k: "ヅ", r: "zu" }, { k: "デ", r: "de" }, { k: "ド", r: "do" },
  { k: "バ", r: "ba" }, { k: "ビ", r: "bi" }, { k: "ブ", r: "bu" }, { k: "ベ", r: "be" }, { k: "ボ", r: "bo" },
  { k: "パ", r: "pa" }, { k: "ピ", r: "pi" }, { k: "プ", r: "pu" }, { k: "ペ", r: "pe" }, { k: "ポ", r: "po" },
];

const KATA_YOON = [
  { k: "キャ", r: "kya" }, { k: "キュ", r: "kyu" }, { k: "キョ", r: "kyo" },
  { k: "シャ", r: "sha" }, { k: "シュ", r: "shu" }, { k: "ショ", r: "sho" },
  { k: "チャ", r: "cha" }, { k: "チュ", r: "chu" }, { k: "チョ", r: "cho" },
  { k: "ニャ", r: "nya" }, { k: "ニュ", r: "nyu" }, { k: "ニョ", r: "nyo" },
  { k: "リャ", r: "rya" }, { k: "リュ", r: "ryu" }, { k: "リョ", r: "ryo" },
  { k: "ジャ", r: "ja" },  { k: "ジュ", r: "ju" },  { k: "ジョ", r: "jo" },
];

const KANA_GROUPS = [
  { key: "hira_base",    label: "Hiragana de base", set: "hira", data: HIRA_BASE },
  { key: "hira_dakuten", label: "Hiragana (゛゜)",   set: "hira", data: HIRA_DAKUTEN },
  { key: "hira_yoon",    label: "Hiragana combinés", set: "hira", data: HIRA_YOON },
  { key: "kata_base",    label: "Katakana de base", set: "kata", data: KATA_BASE },
  { key: "kata_dakuten", label: "Katakana (゛゜)",   set: "kata", data: KATA_DAKUTEN },
  { key: "kata_yoon",    label: "Katakana combinés", set: "kata", data: KATA_YOON },
];

/* ---------- VOCABULAIRE par thème, avec phrases d'exemple ---------- */
const VOCAB = [
  // Salutations & politesse
  { jp: "こんにちは", kana: "こんにちは", romaji: "konnichiwa", fr: "bonjour", theme: "salutations",
    ex: { jp: "こんにちは、元気ですか？", fr: "Bonjour, comment ça va ?" } },
  { jp: "おはよう", kana: "おはよう", romaji: "ohayō", fr: "bonjour (matin)", theme: "salutations",
    ex: { jp: "おはようございます。", fr: "Bonjour (poli, le matin)." } },
  { jp: "こんばんは", kana: "こんばんは", romaji: "konbanwa", fr: "bonsoir", theme: "salutations",
    ex: { jp: "こんばんは、田中さん。", fr: "Bonsoir, M. Tanaka." } },
  { jp: "さようなら", kana: "さようなら", romaji: "sayōnara", fr: "au revoir", theme: "salutations",
    ex: { jp: "さようなら、また明日。", fr: "Au revoir, à demain." } },
  { jp: "ありがとう", kana: "ありがとう", romaji: "arigatō", fr: "merci", theme: "salutations",
    ex: { jp: "ありがとうございます。", fr: "Merci beaucoup (poli)." } },
  { jp: "すみません", kana: "すみません", romaji: "sumimasen", fr: "excusez-moi / pardon", theme: "salutations",
    ex: { jp: "すみません、トイレはどこですか？", fr: "Excusez-moi, où sont les toilettes ?" } },
  { jp: "はい", kana: "はい", romaji: "hai", fr: "oui", theme: "salutations",
    ex: { jp: "はい、わかりました。", fr: "Oui, j'ai compris." } },
  { jp: "いいえ", kana: "いいえ", romaji: "iie", fr: "non", theme: "salutations",
    ex: { jp: "いいえ、違います。", fr: "Non, ce n'est pas ça." } },

  // Se présenter
  { jp: "はじめまして", kana: "はじめまして", romaji: "hajimemashite", fr: "enchanté", theme: "presentation",
    ex: { jp: "はじめまして、トニーです。", fr: "Enchanté, je suis Tony." } },
  { jp: "名前", kana: "なまえ", romaji: "namae", fr: "nom / prénom", theme: "presentation",
    ex: { jp: "お名前は何ですか？", fr: "Quel est votre nom ?" } },
  { jp: "私", kana: "わたし", romaji: "watashi", fr: "je / moi", theme: "presentation",
    ex: { jp: "私はフランス人です。", fr: "Je suis français." } },
  { jp: "学生", kana: "がくせい", romaji: "gakusei", fr: "étudiant", theme: "presentation",
    ex: { jp: "私は学生です。", fr: "Je suis étudiant." } },
  { jp: "日本語", kana: "にほんご", romaji: "nihongo", fr: "langue japonaise", theme: "presentation",
    ex: { jp: "日本語を勉強しています。", fr: "J'étudie le japonais." } },

  // Nombres
  { jp: "一", kana: "いち", romaji: "ichi", fr: "un (1)", theme: "nombres",
    ex: { jp: "りんごを一つください。", fr: "Une pomme, s'il vous plaît." } },
  { jp: "二", kana: "に", romaji: "ni", fr: "deux (2)", theme: "nombres",
    ex: { jp: "二人です。", fr: "Nous sommes deux." } },
  { jp: "三", kana: "さん", romaji: "san", fr: "trois (3)", theme: "nombres",
    ex: { jp: "三時です。", fr: "Il est trois heures." } },
  { jp: "四", kana: "よん", romaji: "yon", fr: "quatre (4)", theme: "nombres",
    ex: { jp: "四階です。", fr: "C'est au quatrième étage." } },
  { jp: "五", kana: "ご", romaji: "go", fr: "cinq (5)", theme: "nombres",
    ex: { jp: "五分待ってください。", fr: "Attendez cinq minutes." } },
  { jp: "六", kana: "ろく", romaji: "roku", fr: "six (6)", theme: "nombres",
    ex: { jp: "六時に会いましょう。", fr: "Rencontrons-nous à six heures." } },
  { jp: "七", kana: "なな", romaji: "nana", fr: "sept (7)", theme: "nombres",
    ex: { jp: "七月です。", fr: "C'est le mois de juillet." } },
  { jp: "八", kana: "はち", romaji: "hachi", fr: "huit (8)", theme: "nombres",
    ex: { jp: "八百円です。", fr: "Ça fait 800 yens." } },
  { jp: "九", kana: "きゅう", romaji: "kyū", fr: "neuf (9)", theme: "nombres",
    ex: { jp: "九時に始まります。", fr: "Ça commence à neuf heures." } },
  { jp: "十", kana: "じゅう", romaji: "jū", fr: "dix (10)", theme: "nombres",
    ex: { jp: "十分かかります。", fr: "Ça prend dix minutes." } },

  // Nourriture
  { jp: "水", kana: "みず", romaji: "mizu", fr: "eau", theme: "nourriture",
    ex: { jp: "水をください。", fr: "De l'eau, s'il vous plaît." } },
  { jp: "お茶", kana: "おちゃ", romaji: "ocha", fr: "thé", theme: "nourriture",
    ex: { jp: "お茶はいかがですか？", fr: "Un thé ?" } },
  { jp: "ご飯", kana: "ごはん", romaji: "gohan", fr: "riz / repas", theme: "nourriture",
    ex: { jp: "ご飯を食べましょう。", fr: "Mangeons." } },
  { jp: "寿司", kana: "すし", romaji: "sushi", fr: "sushi", theme: "nourriture",
    ex: { jp: "寿司が好きです。", fr: "J'aime les sushis." } },
  { jp: "おいしい", kana: "おいしい", romaji: "oishii", fr: "délicieux", theme: "nourriture",
    ex: { jp: "とてもおいしいです！", fr: "C'est très bon !" } },
  { jp: "コーヒー", kana: "コーヒー", romaji: "kōhī", fr: "café", theme: "nourriture",
    ex: { jp: "コーヒーを一つください。", fr: "Un café, s'il vous plaît." } },

  // Voyage & ville
  { jp: "駅", kana: "えき", romaji: "eki", fr: "gare / station", theme: "voyage",
    ex: { jp: "駅はどこですか？", fr: "Où est la gare ?" } },
  { jp: "電車", kana: "でんしゃ", romaji: "densha", fr: "train", theme: "voyage",
    ex: { jp: "電車で行きます。", fr: "J'y vais en train." } },
  { jp: "ホテル", kana: "ホテル", romaji: "hoteru", fr: "hôtel", theme: "voyage",
    ex: { jp: "ホテルを探しています。", fr: "Je cherche un hôtel." } },
  { jp: "いくら", kana: "いくら", romaji: "ikura", fr: "combien (prix)", theme: "voyage",
    ex: { jp: "これはいくらですか？", fr: "Combien ça coûte ?" } },
  { jp: "どこ", kana: "どこ", romaji: "doko", fr: "où", theme: "voyage",
    ex: { jp: "出口はどこですか？", fr: "Où est la sortie ?" } },
  { jp: "右", kana: "みぎ", romaji: "migi", fr: "droite", theme: "voyage",
    ex: { jp: "右に曲がってください。", fr: "Tournez à droite." } },
  { jp: "左", kana: "ひだり", romaji: "hidari", fr: "gauche", theme: "voyage",
    ex: { jp: "左に銀行があります。", fr: "Il y a une banque à gauche." } },

  // Temps & quotidien
  { jp: "今日", kana: "きょう", romaji: "kyō", fr: "aujourd'hui", theme: "quotidien",
    ex: { jp: "今日は暑いです。", fr: "Il fait chaud aujourd'hui." } },
  { jp: "明日", kana: "あした", romaji: "ashita", fr: "demain", theme: "quotidien",
    ex: { jp: "また明日。", fr: "À demain." } },
  { jp: "時間", kana: "じかん", romaji: "jikan", fr: "temps / heure", theme: "quotidien",
    ex: { jp: "時間がありません。", fr: "Je n'ai pas le temps." } },
  { jp: "好き", kana: "すき", romaji: "suki", fr: "aimer / préférer", theme: "quotidien",
    ex: { jp: "音楽が好きです。", fr: "J'aime la musique." } },
  { jp: "大丈夫", kana: "だいじょうぶ", romaji: "daijōbu", fr: "ça va / d'accord", theme: "quotidien",
    ex: { jp: "大丈夫ですか？", fr: "Est-ce que ça va ?" } },

  // Expressions utiles
  { jp: "わかりません", kana: "わかりません", romaji: "wakarimasen", fr: "je ne comprends pas", theme: "expressions",
    ex: { jp: "すみません、わかりません。", fr: "Désolé, je ne comprends pas." } },
  { jp: "もう一度", kana: "もういちど", romaji: "mō ichido", fr: "encore une fois", theme: "expressions",
    ex: { jp: "もう一度お願いします。", fr: "Encore une fois, s'il vous plaît." } },
  { jp: "ゆっくり", kana: "ゆっくり", romaji: "yukkuri", fr: "lentement", theme: "expressions",
    ex: { jp: "ゆっくり話してください。", fr: "Parlez lentement, s'il vous plaît." } },
  { jp: "お願いします", kana: "おねがいします", romaji: "onegaishimasu", fr: "s'il vous plaît", theme: "expressions",
    ex: { jp: "これをお願いします。", fr: "Ceci, s'il vous plaît." } },
  { jp: "助けて", kana: "たすけて", romaji: "tasukete", fr: "à l'aide !", theme: "expressions",
    ex: { jp: "助けて！", fr: "À l'aide !" } },
];

const VOCAB_THEMES = [
  { key: "salutations",  emoji: "👋", label: "Salutations & politesse" },
  { key: "presentation", emoji: "🙋", label: "Se présenter" },
  { key: "nombres",      emoji: "🔢", label: "Nombres" },
  { key: "nourriture",   emoji: "🍜", label: "Manger & boire" },
  { key: "voyage",       emoji: "🚉", label: "Voyage & ville" },
  { key: "quotidien",    emoji: "🕒", label: "Temps & quotidien" },
  { key: "expressions",  emoji: "💬", label: "Expressions utiles" },
];

window.KANA_GROUPS = KANA_GROUPS;
window.VOCAB = VOCAB;
window.VOCAB_THEMES = VOCAB_THEMES;
