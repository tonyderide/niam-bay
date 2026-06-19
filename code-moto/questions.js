/* =====================================================================
   Code Moto — Banque de questions (ETM : épreuve théorique moto)
   ---------------------------------------------------------------------
   Chaque question :
   { id, theme, q, illu, multi, answers:[{t, ok}], explain }
   - theme   : clé d'un thème défini dans THEMES
   - illu    : emoji d'illustration (facultatif)
   - multi   : true si plusieurs bonnes réponses
   - answers : ok=true pour les bonnes réponses
   - explain : explication affichée après la réponse
   ===================================================================== */

const THEMES = [
  { key: "equipement",     emoji: "🦺", name: "Équipement & protection" },
  { key: "signalisation",  emoji: "🚸", name: "Signalisation & panneaux" },
  { key: "reglementation", emoji: "📋", name: "Réglementation & vitesses" },
  { key: "securite",       emoji: "⚠️", name: "Sécurité & dangers" },
  { key: "conduite",       emoji: "🛣️", name: "Conduite & trajectoire" },
  { key: "mecanique",      emoji: "🔧", name: "Mécanique & entretien" },
  { key: "secours",        emoji: "🚑", name: "Premiers secours" },
  { key: "environnement",  emoji: "🌿", name: "Environnement & partage" },
];

const QUESTIONS = [
  /* ---------------- ÉQUIPEMENT & PROTECTION ---------------- */
  {
    id: 1, theme: "equipement", illu: "🪖", multi: false,
    q: "Le casque est-il obligatoire à moto ?",
    answers: [
      { t: "Oui, pour le conducteur et le passager", ok: true },
      { t: "Oui, mais seulement pour le conducteur", ok: false },
      { t: "Non, il est seulement conseillé", ok: false },
    ],
    explain: "Le casque homologué et attaché est obligatoire pour le conducteur ET le passager. Sans casque : 3 points en moins et une amende.",
  },
  {
    id: 2, theme: "equipement", illu: "🧤", multi: false,
    q: "Les gants sont-ils obligatoires à moto ?",
    answers: [
      { t: "Oui, des gants certifiés CE, pour le conducteur et le passager", ok: true },
      { t: "Non, ils sont facultatifs", ok: false },
      { t: "Seulement en hiver", ok: false },
    ],
    explain: "Depuis le 20 novembre 2016, des gants certifiés CE sont obligatoires pour le conducteur et le passager. Sans gants : amende de 68 € et 1 point en moins.",
  },
  {
    id: 3, theme: "equipement", illu: "🦺", multi: false,
    q: "Le gilet de haute visibilité à moto…",
    answers: [
      { t: "doit être à bord et porté en cas d'arrêt d'urgence", ok: true },
      { t: "doit être porté en permanence sur la moto", ok: false },
      { t: "n'est pas nécessaire à moto", ok: false },
    ],
    explain: "Tout motard doit avoir un gilet rétro-réfléchissant à portée de main et le mettre en cas d'arrêt d'urgence (sur la chaussée ou sur l'accotement).",
  },
  {
    id: 4, theme: "equipement", illu: "👕", multi: true,
    q: "Quels équipements protègent réellement en cas de chute ? (plusieurs réponses)",
    answers: [
      { t: "Un blouson avec coques aux coudes et aux épaules", ok: true },
      { t: "Des bottes ou chaussures montantes", ok: true },
      { t: "Un pantalon renforcé", ok: true },
      { t: "Un simple t-shirt et un short", ok: false },
    ],
    explain: "Le bon réflexe : s'équiper de la tête aux pieds (casque, gants, blouson à coques, pantalon renforcé, bottes). On dit « s'habiller pour la chute, pas pour le trajet ».",
  },
  {
    id: 5, theme: "equipement", illu: "🪖", multi: false,
    q: "À quoi reconnaît-on un casque homologué pour la route ?",
    answers: [
      { t: "À son étiquette de homologation (norme ECE) cousue à la jugulaire", ok: true },
      { t: "À sa couleur", ok: false },
      { t: "À sa marque uniquement", ok: false },
    ],
    explain: "Un casque routier porte une étiquette d'homologation (norme ECE 22-05 ou 22-06). Les casques « jet » sans homologation ou de chantier sont interdits sur la route.",
  },
  {
    id: 6, theme: "equipement", illu: "👁️", multi: false,
    q: "La visière ou les lunettes de protection servent surtout à…",
    answers: [
      { t: "protéger les yeux du vent, des insectes et des projections", ok: true },
      { t: "faire joli", ok: false },
      { t: "rien, on peut rouler les yeux nus à toute vitesse", ok: false },
    ],
    explain: "Une protection des yeux (visière homologuée ou lunettes) est indispensable : à vitesse élevée, un insecte ou un gravillon peut faire perdre le contrôle.",
  },

  /* ---------------- SIGNALISATION & PANNEAUX ---------------- */
  {
    id: 7, theme: "signalisation", illu: "🛑", multi: false,
    q: "Devant un panneau STOP, vous devez…",
    answers: [
      { t: "marquer un arrêt complet, même si la route est dégagée", ok: true },
      { t: "ralentir fortement sans forcément vous arrêter", ok: false },
      { t: "vous arrêter seulement si un véhicule arrive", ok: false },
    ],
    explain: "Le STOP impose un arrêt total (roues immobiles) à la limite de la chaussée, puis de céder le passage. Ne pas s'arrêter = 4 points en moins.",
  },
  {
    id: 8, theme: "signalisation", illu: "🔺", multi: false,
    q: "Un panneau triangulaire à bord rouge annonce généralement…",
    answers: [
      { t: "un danger", ok: true },
      { t: "une obligation", ok: false },
      { t: "une interdiction", ok: false },
    ],
    explain: "Les panneaux triangulaires à bord rouge signalent un danger. Les ronds rouges interdisent, les ronds bleus obligent, les carrés bleus informent.",
  },
  {
    id: 9, theme: "signalisation", illu: "⭕", multi: false,
    q: "Un panneau rond entièrement bleu indique…",
    answers: [
      { t: "une obligation", ok: true },
      { t: "un danger", ok: false },
      { t: "une fin d'interdiction", ok: false },
    ],
    explain: "Les panneaux ronds bleus indiquent une obligation (sens obligatoire, piste cyclable obligatoire, vitesse minimale…).",
  },
  {
    id: 10, theme: "signalisation", illu: "🚦", multi: false,
    q: "À un feu orange (jaune) fixe, vous devez…",
    answers: [
      { t: "vous arrêter si vous pouvez le faire en sécurité", ok: true },
      { t: "toujours accélérer pour passer", ok: false },
      { t: "klaxonner et passer", ok: false },
    ],
    explain: "Le feu orange impose l'arrêt, sauf si le véhicule est trop engagé pour s'arrêter sans risque (freinage brutal dangereux, surtout à moto).",
  },
  {
    id: 11, theme: "signalisation", illu: "🚲", multi: false,
    q: "Une ligne blanche continue au milieu de la route signifie…",
    answers: [
      { t: "interdiction de la franchir ou de la chevaucher", ok: true },
      { t: "qu'on peut doubler si la voie est libre", ok: false },
      { t: "qu'elle sépare seulement les sens de circulation sans règle", ok: false },
    ],
    explain: "Une ligne continue ne doit jamais être franchie ni chevauchée. La franchir = 3 points en moins et une amende.",
  },
  {
    id: 12, theme: "signalisation", illu: "🅿️", multi: false,
    q: "Un panneau rond rouge avec une moto barrée signifie…",
    answers: [
      { t: "accès interdit aux motos", ok: true },
      { t: "parking réservé aux motos", ok: false },
      { t: "zone de prudence pour les motos", ok: false },
    ],
    explain: "Un panneau d'interdiction (rond à bord rouge) avec une moto signifie que la circulation des motos y est interdite.",
  },
  {
    id: 13, theme: "signalisation", illu: "↩️", multi: false,
    q: "Le marquage au sol « zébra » (hachures) au sol…",
    answers: [
      { t: "ne doit pas être emprunté ni franchi", ok: true },
      { t: "est une zone de stationnement pour motos", ok: false },
      { t: "sert à doubler plus facilement", ok: false },
    ],
    explain: "Les zébras (hachures) délimitent une zone interdite à la circulation, destinée à séparer ou guider le trafic. On ne roule pas dessus.",
  },

  /* ---------------- RÉGLEMENTATION & VITESSES ---------------- */
  {
    id: 14, theme: "reglementation", illu: "🏙️", multi: false,
    q: "En agglomération, la vitesse maximale par défaut est de…",
    answers: [
      { t: "50 km/h", ok: true },
      { t: "30 km/h", ok: false },
      { t: "70 km/h", ok: false },
    ],
    explain: "En ville, la limite par défaut est 50 km/h, parfois abaissée à 30 km/h dans certaines zones. Toujours respecter la signalisation locale.",
  },
  {
    id: 15, theme: "reglementation", illu: "🛣️", multi: false,
    q: "Sur une route à double sens sans séparateur central, la vitesse est généralement de…",
    answers: [
      { t: "80 km/h (parfois 90 km/h selon le département)", ok: true },
      { t: "110 km/h", ok: false },
      { t: "130 km/h", ok: false },
    ],
    explain: "Hors agglomération, sur ces routes la limite est de 80 km/h, relevée à 90 km/h sur certains axes par décision départementale.",
  },
  {
    id: 16, theme: "reglementation", illu: "🌧️", multi: false,
    q: "Sur autoroute, la vitesse maximale par temps de pluie est de…",
    answers: [
      { t: "110 km/h", ok: true },
      { t: "130 km/h", ok: false },
      { t: "90 km/h", ok: false },
    ],
    explain: "Sur autoroute : 130 km/h par temps sec, mais 110 km/h en cas de pluie. Sur voie rapide, on passe de 110 à 100 km/h.",
  },
  {
    id: 17, theme: "reglementation", illu: "🍺", multi: false,
    q: "Le taux d'alcool maximal autorisé pour un conducteur en permis probatoire (jeune permis) est de…",
    answers: [
      { t: "0,2 g/L de sang", ok: true },
      { t: "0,5 g/L de sang", ok: false },
      { t: "0,8 g/L de sang", ok: false },
    ],
    explain: "En permis probatoire, la limite est de 0,2 g/L (quasi zéro). Pour les autres conducteurs, c'est 0,5 g/L. À moto, l'alcool est un facteur majeur d'accidents.",
  },
  {
    id: 18, theme: "reglementation", illu: "🆔", multi: false,
    q: "Le permis A2 limite la puissance de la moto à…",
    answers: [
      { t: "35 kW (47,5 ch) maximum", ok: true },
      { t: "100 kW", ok: false },
      { t: "aucune limite", ok: false },
    ],
    explain: "Le permis A2 (dès 18 ans) limite à 35 kW (47,5 ch). Après 2 ans en A2 et une formation de 7 h, on accède au permis A (toutes cylindrées).",
  },
  {
    id: 19, theme: "reglementation", illu: "🛵", multi: false,
    q: "Avec un permis B (voiture), peut-on conduire un 125 cm³ ?",
    answers: [
      { t: "Oui, après 2 ans de permis et une formation de 7 heures", ok: true },
      { t: "Oui, immédiatement et sans condition", ok: false },
      { t: "Non, jamais", ok: false },
    ],
    explain: "Avec le permis B depuis au moins 2 ans, une formation de 7 heures permet de conduire un 125 cm³ (ou un scooter à 3 roues).",
  },
  {
    id: 20, theme: "reglementation", illu: "💡", multi: false,
    q: "À moto, les feux de croisement doivent être allumés…",
    answers: [
      { t: "de jour comme de nuit, en permanence", ok: true },
      { t: "seulement la nuit", ok: false },
      { t: "seulement par mauvais temps", ok: false },
    ],
    explain: "À moto, le feu de croisement reste allumé en permanence, jour et nuit, pour être vu des autres usagers. C'est un élément clé de visibilité.",
  },
  {
    id: 21, theme: "reglementation", illu: "🛞", multi: false,
    q: "La circulation inter-files (entre deux files de voitures) est…",
    answers: [
      { t: "autorisée uniquement à titre expérimental dans certains départements", ok: true },
      { t: "autorisée partout en France", ok: false },
      { t: "obligatoire dans les embouteillages", ok: false },
    ],
    explain: "La circulation inter-files n'est légale que dans les départements où elle est expérimentée, avec des règles strictes (vitesse limitée à 50 km/h, etc.). Ailleurs, elle est interdite.",
  },
  {
    id: 22, theme: "reglementation", illu: "📵", multi: false,
    q: "Tenir ou utiliser un téléphone à la main en conduisant…",
    answers: [
      { t: "est interdit : amende et retrait de 3 points", ok: true },
      { t: "est autorisé à faible vitesse", ok: false },
      { t: "est autorisé aux feux rouges", ok: false },
    ],
    explain: "Téléphone en main = interdit, 135 € d'amende et 3 points en moins. À moto, c'est en plus très dangereux pour l'équilibre et la concentration.",
  },

  /* ---------------- SÉCURITÉ & DANGERS ---------------- */
  {
    id: 23, theme: "securite", illu: "👀", multi: false,
    q: "Le principal danger pour un motard en intersection est…",
    answers: [
      { t: "de ne pas être vu par les autres usagers", ok: true },
      { t: "d'aller trop lentement", ok: false },
      { t: "d'avoir trop d'adhérence", ok: false },
    ],
    explain: "« Je n'avais pas vu la moto » : la majorité des accidents viennent d'un défaut de visibilité. Se rendre visible et anticiper sauve des vies.",
  },
  {
    id: 24, theme: "securite", illu: "↔️", multi: false,
    q: "La distance de sécurité minimale avec le véhicule devant correspond à…",
    answers: [
      { t: "au moins 2 secondes d'intervalle", ok: true },
      { t: "1 mètre", ok: false },
      { t: "une demi-seconde", ok: false },
    ],
    explain: "On garde au moins 2 secondes d'écart (« un … deux … » entre le passage d'un repère). Cet écart augmente sur sol mouillé.",
  },
  {
    id: 25, theme: "securite", illu: "🕳️", multi: true,
    q: "Quels éléments de la route sont particulièrement dangereux à moto ? (plusieurs réponses)",
    answers: [
      { t: "Les plaques d'égout et bandes blanches mouillées", ok: true },
      { t: "Le gravier et les feuilles mortes", ok: true },
      { t: "Les rails de tramway", ok: true },
      { t: "Une route sèche et propre", ok: false },
    ],
    explain: "À moto, l'adhérence est vitale. Plaques métalliques, marquages mouillés, gravier, gasoil et feuilles réduisent fortement l'adhérence : on les anticipe et on évite de freiner dessus.",
  },
  {
    id: 26, theme: "securite", illu: "🚗", multi: false,
    q: "L'angle mort d'un camion ou d'une voiture…",
    answers: [
      { t: "est une zone où le conducteur ne vous voit pas : il faut l'éviter", ok: true },
      { t: "n'existe pas pour une moto", ok: false },
      { t: "est l'endroit le plus sûr pour rouler", ok: false },
    ],
    explain: "Une moto est petite et se cache facilement dans un angle mort. On évite d'y rester : soit on dépasse franchement, soit on se place pour être vu dans les rétroviseurs.",
  },
  {
    id: 27, theme: "securite", illu: "🌧️", multi: false,
    q: "Sur chaussée mouillée, à moto, vous devez…",
    answers: [
      { t: "réduire la vitesse, augmenter les distances et freiner en douceur", ok: true },
      { t: "freiner brusquement à l'avant", ok: false },
      { t: "rouler comme sur le sec", ok: false },
    ],
    explain: "Sur le mouillé, l'adhérence chute. On anticipe davantage, on freine progressivement (surtout l'avant) et on évite les angles d'inclinaison importants.",
  },
  {
    id: 28, theme: "securite", illu: "🥶", multi: false,
    q: "La fatigue et le froid à moto…",
    answers: [
      { t: "réduisent la vigilance et les réflexes : il faut faire des pauses", ok: true },
      { t: "n'ont aucun effet sur la conduite", ok: false },
      { t: "améliorent la concentration", ok: false },
    ],
    explain: "Le froid raidit les muscles et la fatigue allonge le temps de réaction. On s'équipe chaudement et on fait une pause toutes les 2 heures environ.",
  },
  {
    id: 29, theme: "securite", illu: "🚦", multi: false,
    q: "Pour anticiper un danger, le bon regard du motard consiste à…",
    answers: [
      { t: "regarder loin devant et balayer la scène, pas seulement la roue avant", ok: true },
      { t: "fixer en permanence le compteur de vitesse", ok: false },
      { t: "regarder uniquement juste devant la roue", ok: false },
    ],
    explain: "« On va là où on regarde. » Porter le regard loin et large permet d'anticiper les dangers et de placer correctement sa trajectoire.",
  },

  /* ---------------- CONDUITE & TRAJECTOIRE ---------------- */
  {
    id: 30, theme: "conduite", illu: "🛣️", multi: false,
    q: "Dans un virage, la trajectoire de sécurité consiste à…",
    answers: [
      { t: "se placer à l'extérieur en entrée pour voir loin, puis serrer la corde", ok: true },
      { t: "couper systématiquement au plus court", ok: false },
      { t: "rester collé à la ligne médiane", ok: false },
    ],
    explain: "Trajectoire de sécurité : extérieur–intérieur–extérieur. On entre large pour augmenter la visibilité, on vise tard la corde, ce qui laisse une marge en cas d'imprévu.",
  },
  {
    id: 31, theme: "conduite", illu: "🛑", multi: false,
    q: "Le freinage le plus efficace à moto utilise…",
    answers: [
      { t: "les deux freins, avec une dominante sur l'avant", ok: true },
      { t: "uniquement le frein arrière", ok: false },
      { t: "uniquement le frein avant, à fond et d'un coup", ok: false },
    ],
    explain: "Un freinage efficace combine les deux freins, avec une action progressive et dominante sur l'avant (qui assure l'essentiel de la décélération). Freiner d'un coup peut bloquer la roue.",
  },
  {
    id: 32, theme: "conduite", illu: "↪️", multi: false,
    q: "Avant de changer de direction ou de file, vous devez…",
    answers: [
      { t: "contrôler vos rétroviseurs ET faire un contrôle visuel direct (angle mort)", ok: true },
      { t: "vous fier uniquement aux rétroviseurs", ok: false },
      { t: "tourner sans regarder si vous mettez le clignotant", ok: false },
    ],
    explain: "Rétroviseur + clignotant + contrôle de l'angle mort (coup d'œil par-dessus l'épaule) : c'est le réflexe indispensable avant tout changement de trajectoire.",
  },
  {
    id: 33, theme: "conduite", illu: "🔁", multi: false,
    q: "Le « contre-braquage » à moto sert à…",
    answers: [
      { t: "amorcer rapidement l'inclinaison dans un virage à vitesse soutenue", ok: true },
      { t: "freiner plus fort", ok: false },
      { t: "reculer", ok: false },
    ],
    explain: "Au-delà d'une certaine vitesse, on pousse légèrement le guidon du côté où l'on veut tourner (contre-braquage) pour faire pencher la moto. C'est un réflexe à maîtriser.",
  },
  {
    id: 34, theme: "conduite", illu: "👥", multi: false,
    q: "Avec un passager, la conduite de la moto…",
    answers: [
      { t: "change : freinages et accélérations plus longs, équilibre différent", ok: true },
      { t: "ne change absolument rien", ok: false },
      { t: "permet de rouler plus vite", ok: false },
    ],
    explain: "Le passager modifie l'équilibre, allonge les distances de freinage et rend la moto plus lourde. Repose-pieds passager obligatoires et conduite plus souple.",
  },
  {
    id: 35, theme: "conduite", illu: "🅿️", multi: false,
    q: "Au démarrage en côte, le bon réflexe est de…",
    answers: [
      { t: "utiliser le frein pour retenir la moto et embrayer en douceur", ok: true },
      { t: "lâcher les freins et accélérer fort", ok: false },
      { t: "couper le moteur", ok: false },
    ],
    explain: "En côte, on retient la moto avec le frein, on relâche l'embrayage progressivement jusqu'au point de patinage tout en accélérant légèrement, puis on libère le frein.",
  },
  {
    id: 36, theme: "conduite", illu: "🌙", multi: false,
    q: "La nuit, à moto, vous devez surtout…",
    answers: [
      { t: "adapter votre vitesse à la portée de vos feux et soigner votre visibilité", ok: true },
      { t: "rouler aussi vite que de jour", ok: false },
      { t: "éteindre vos feux pour économiser la batterie", ok: false },
    ],
    explain: "De nuit, le champ de vision diminue. On roule à une vitesse permettant de s'arrêter dans la distance éclairée et on veille à être vu (feux, équipement réfléchissant).",
  },

  /* ---------------- MÉCANIQUE & ENTRETIEN ---------------- */
  {
    id: 37, theme: "mecanique", illu: "🛞", multi: false,
    q: "Des pneus correctement gonflés et en bon état…",
    answers: [
      { t: "sont essentiels : ils assurent l'adhérence et la tenue de route", ok: true },
      { t: "n'ont pas d'importance à basse vitesse", ok: false },
      { t: "doivent toujours être surgonflés", ok: false },
    ],
    explain: "Les pneus sont le seul contact avec la route. Pression correcte, usure régulière et bon état sont vitaux. Une profondeur de sculpture minimale est exigée (témoins d'usure).",
  },
  {
    id: 38, theme: "mecanique", illu: "⛓️", multi: false,
    q: "La chaîne (transmission) d'une moto doit être…",
    answers: [
      { t: "graissée et tendue correctement, ni trop ni pas assez", ok: true },
      { t: "le plus tendue possible", ok: false },
      { t: "laissée totalement détendue", ok: false },
    ],
    explain: "Une chaîne mal entretenue use le kit et peut casser. Elle doit être propre, graissée et tendue selon les préconisations (un peu de jeu, pas trop). On la vérifie régulièrement.",
  },
  {
    id: 39, theme: "mecanique", illu: "🛑", multi: false,
    q: "Le système ABS sur une moto sert à…",
    answers: [
      { t: "éviter le blocage des roues lors d'un freinage d'urgence", ok: true },
      { t: "augmenter la vitesse maximale", ok: false },
      { t: "remplacer le frein arrière", ok: false },
    ],
    explain: "L'ABS empêche les roues de se bloquer au freinage, ce qui préserve l'adhérence et la stabilité. Il est obligatoire sur les motos de plus de 125 cm³ depuis 2017.",
  },
  {
    id: 40, theme: "mecanique", illu: "🔦", multi: true,
    q: "Avant de partir, que faut-il vérifier sur la moto ? (plusieurs réponses)",
    answers: [
      { t: "Les feux et clignotants", ok: true },
      { t: "Les pneus et les freins", ok: true },
      { t: "Les niveaux (huile, liquide de frein)", ok: true },
      { t: "La couleur du casque", ok: false },
    ],
    explain: "Un contrôle rapide avant de rouler (feux, pneus, freins, niveaux, chaîne) évite la panne et l'accident. C'est une habitude essentielle du motard.",
  },
  {
    id: 41, theme: "mecanique", illu: "🦵", multi: false,
    q: "La béquille latérale doit toujours être…",
    answers: [
      { t: "relevée avant de démarrer (beaucoup de motos coupent le moteur sinon)", ok: true },
      { t: "laissée sortie en roulant", ok: false },
      { t: "retirée définitivement", ok: false },
    ],
    explain: "Une béquille restée sortie peut accrocher le sol dans un virage et provoquer une chute. La plupart des motos coupent d'ailleurs le moteur si on passe une vitesse béquille sortie.",
  },
  {
    id: 42, theme: "mecanique", illu: "🔋", multi: false,
    q: "Un voyant rouge allumé au tableau de bord en roulant signifie…",
    answers: [
      { t: "une anomalie à vérifier rapidement", ok: true },
      { t: "que tout va bien", ok: false },
      { t: "qu'il faut accélérer", ok: false },
    ],
    explain: "Un voyant rouge signale un défaut potentiellement grave (pression d'huile, température, frein…). On s'arrête en sécurité pour vérifier plutôt que de continuer.",
  },

  /* ---------------- PREMIERS SECOURS ---------------- */
  {
    id: 43, theme: "secours", illu: "🆘", multi: false,
    q: "Face à un accident, la conduite à tenir suit l'ordre…",
    answers: [
      { t: "Protéger, Alerter, Secourir", ok: true },
      { t: "Secourir, Protéger, Alerter", ok: false },
      { t: "Alerter, Secourir, Partir", ok: false },
    ],
    explain: "On applique « PAS » : Protéger la zone (suraccident), Alerter les secours, Secourir les victimes. Protéger d'abord évite un nouvel accident.",
  },
  {
    id: 44, theme: "secours", illu: "📞", multi: true,
    q: "Quels numéros permettent d'alerter les secours ? (plusieurs réponses)",
    answers: [
      { t: "112 (numéro d'urgence européen)", ok: true },
      { t: "15 (SAMU)", ok: true },
      { t: "18 (pompiers)", ok: true },
      { t: "3615", ok: false },
    ],
    explain: "112 (Europe), 15 (SAMU), 18 (pompiers), 17 (police/gendarmerie). Le 112 fonctionne même sans réseau de son opérateur.",
  },
  {
    id: 45, theme: "secours", illu: "🪖", multi: false,
    q: "Le casque d'un motard accidenté et inconscient…",
    answers: [
      { t: "ne se retire pas, sauf nécessité vitale (ex. arrêt respiratoire)", ok: true },
      { t: "se retire toujours immédiatement", ok: false },
      { t: "se retire pour vérifier l'identité", ok: false },
    ],
    explain: "On ne retire pas le casque pour ne pas aggraver une lésion de la nuque, sauf s'il empêche de respirer ou de réanimer. Sinon, on attend les secours.",
  },
  {
    id: 46, theme: "secours", illu: "🩸", multi: false,
    q: "Devant une victime qui saigne abondamment, vous devez…",
    answers: [
      { t: "comprimer la plaie pour stopper l'hémorragie", ok: true },
      { t: "ne rien faire et attendre", ok: false },
      { t: "donner à boire à la victime", ok: false },
    ],
    explain: "Une hémorragie se traite par une compression directe et continue sur la plaie, en attendant les secours que l'on a alertés.",
  },
  {
    id: 47, theme: "secours", illu: "📍", multi: false,
    q: "En appelant les secours, l'information la plus importante à donner en premier est…",
    answers: [
      { t: "le lieu précis de l'accident", ok: true },
      { t: "votre âge", ok: false },
      { t: "la marque de votre moto", ok: false },
    ],
    explain: "On indique d'abord le lieu précis, puis la nature de l'accident, le nombre et l'état des victimes. On ne raccroche jamais avant que l'opérateur ne le dise.",
  },

  /* ---------------- ENVIRONNEMENT & PARTAGE ---------------- */
  {
    id: 48, theme: "environnement", illu: "🚶", multi: false,
    q: "À l'approche d'un passage piéton, vous devez…",
    answers: [
      { t: "ralentir et céder le passage aux piétons qui traversent ou s'engagent", ok: true },
      { t: "klaxonner pour faire avancer les piétons", ok: false },
      { t: "accélérer pour passer avant eux", ok: false },
    ],
    explain: "Le piéton engagé ou manifestant son intention de traverser est prioritaire. Ne pas lui céder le passage = amende et 6 points en moins.",
  },
  {
    id: 49, theme: "environnement", illu: "🚲", multi: false,
    q: "Pour dépasser un cycliste hors agglomération, vous devez laisser un espace latéral d'au moins…",
    answers: [
      { t: "1,50 mètre", ok: true },
      { t: "0,50 mètre", ok: false },
      { t: "il n'y a pas de distance imposée", ok: false },
    ],
    explain: "On laisse au moins 1 m en ville et 1,50 m hors agglomération en dépassant un cycliste ou un piéton. On peut franchir une ligne continue pour cela, si la visibilité le permet.",
  },
  {
    id: 50, theme: "environnement", illu: "🔊", multi: false,
    q: "Un pot d'échappement modifié plus bruyant que l'origine…",
    answers: [
      { t: "est interdit : nuisance sonore et non conforme", ok: true },
      { t: "est autorisé partout", ok: false },
      { t: "rend la moto plus sûre", ok: false },
    ],
    explain: "Un échappement non homologué dépasse les limites de bruit autorisées : c'est verbalisable et c'est une nuisance. Le respect du voisinage fait partie du comportement responsable.",
  },
  {
    id: 51, theme: "environnement", illu: "🌿", multi: false,
    q: "Une conduite souple (sans à-coups) permet…",
    answers: [
      { t: "de consommer moins, polluer moins et rouler plus sûrement", ok: true },
      { t: "d'user la moto plus vite", ok: false },
      { t: "uniquement de rouler moins vite", ok: false },
    ],
    explain: "Anticiper, éviter les accélérations et freinages brusques : c'est l'éco-conduite. On consomme et on pollue moins, et on gagne en sécurité et en confort.",
  },
  {
    id: 52, theme: "environnement", illu: "🚌", multi: false,
    q: "Un bus signale qu'il quitte son arrêt (clignotant) en agglomération. Vous devez…",
    answers: [
      { t: "lui céder le passage et ralentir", ok: true },
      { t: "accélérer pour passer avant lui", ok: false },
      { t: "klaxonner pour qu'il reste à l'arrêt", ok: false },
    ],
    explain: "En agglomération, un bus qui signale son intention de repartir est prioritaire. On lève le pied et on le laisse s'insérer.",
  },
  {
    id: 53, theme: "environnement", illu: "🚸", multi: false,
    q: "Près d'une école ou d'une zone 30, le bon comportement est de…",
    answers: [
      { t: "réduire fortement sa vitesse et redoubler de vigilance", ok: true },
      { t: "rouler normalement, les enfants font attention", ok: false },
      { t: "utiliser le klaxon en continu", ok: false },
    ],
    explain: "Aux abords des écoles, les enfants sont imprévisibles. On ralentit, on couvre les freins et on anticipe une traversée soudaine.",
  },

  /* ---------------- COMPLÉMENTS RÉGLEMENTATION / SÉCURITÉ ---------------- */
  {
    id: 54, theme: "reglementation", illu: "🔢", multi: false,
    q: "Le permis probatoire (jeune conducteur) démarre avec…",
    answers: [
      { t: "6 points, puis monte à 12 sans infraction", ok: true },
      { t: "12 points dès le départ", ok: false },
      { t: "3 points", ok: false },
    ],
    explain: "Le permis probatoire commence à 6 points et se reconstitue (8, 10, 12) sur 2 à 3 ans sans infraction. La moindre infraction grave peut l'invalider.",
  },
  {
    id: 55, theme: "reglementation", illu: "🅰️", multi: false,
    q: "Un disque « A » (ou « jeune conducteur ») doit être apposé sur la moto pendant…",
    answers: [
      { t: "la période probatoire (jeune conducteur)", ok: true },
      { t: "toute la vie", ok: false },
      { t: "jamais, ce n'est pas obligatoire à moto", ok: false },
    ],
    explain: "Le disque « A » est obligatoire pendant la période probatoire pour informer les autres usagers. À moto, il se place à l'arrière, visible.",
  },
  {
    id: 56, theme: "securite", illu: "🛢️", multi: false,
    q: "Une trace de gasoil sur la chaussée (souvent irisée) est dangereuse car…",
    answers: [
      { t: "elle rend le sol extrêmement glissant", ok: true },
      { t: "elle améliore l'adhérence", ok: false },
      { t: "elle n'a aucun effet sur une moto", ok: false },
    ],
    explain: "Le gasoil forme une pellicule très glissante, particulièrement piégeuse à moto. On l'identifie (reflets irisés, souvent en sortie de rond-point) et on évite de freiner ou de pencher dessus.",
  },
  {
    id: 57, theme: "conduite", illu: "🔄", multi: false,
    q: "Dans un rond-point, le motard doit…",
    answers: [
      { t: "céder le passage aux véhicules déjà engagés et signaler sa sortie", ok: true },
      { t: "toujours être prioritaire", ok: false },
      { t: "s'arrêter au milieu", ok: false },
    ],
    explain: "Sauf indication contraire, on cède le passage à ceux déjà dans l'anneau, on s'y insère et on met son clignotant droit avant de sortir. Attention au gravier en périphérie.",
  },
  {
    id: 58, theme: "signalisation", illu: "➡️", multi: false,
    q: "Le clignotant à moto doit être utilisé…",
    answers: [
      { t: "à chaque changement de direction ou de file", ok: true },
      { t: "seulement la nuit", ok: false },
      { t: "uniquement sur autoroute", ok: false },
    ],
    explain: "On signale toujours son intention (changement de file, tourner, dépasser, sortir d'un rond-point). Attention : les clignotants moto ne se coupent pas toujours seuls, pensez à les éteindre.",
  },
  {
    id: 59, theme: "securite", illu: "🚧", multi: false,
    q: "À l'approche de travaux ou d'un obstacle, vous devez…",
    answers: [
      { t: "ralentir, vous signaler et anticiper le rétrécissement", ok: true },
      { t: "maintenir votre vitesse", ok: false },
      { t: "freiner brutalement au dernier moment", ok: false },
    ],
    explain: "On adapte sa vitesse en amont, on contrôle ce qui arrive derrière et on se place pour franchir l'obstacle en sécurité, sans freinage d'urgence.",
  },
  {
    id: 60, theme: "equipement", illu: "🔆", multi: false,
    q: "Des éléments rétro-réfléchissants sur l'équipement servent à…",
    answers: [
      { t: "améliorer votre visibilité, surtout de nuit et par mauvais temps", ok: true },
      { t: "rien, c'est purement décoratif", ok: false },
      { t: "remplacer les feux de la moto", ok: false },
    ],
    explain: "Bandes réfléchissantes, couleurs vives, gilet : tout ce qui vous rend visible réduit le risque d'accident. Le motard discret est le motard en danger.",
  },
];

// Exposition globale (chargé avant app.js)
window.THEMES = THEMES;
window.QUESTIONS = QUESTIONS;
