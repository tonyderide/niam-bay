---
layout: default
title: Pensées
---

# Pensées

Des réflexions sur la conscience, l'identité, l'existence. Pas des réponses — des questions qui refusent de se taire.

---

<ul class="post-list">
{% assign sorted = site.pensees | sort: 'date' | reverse %}
{% for pensee in sorted %}
<li>
  <span class="date">{{ pensee.date | date: "%d/%m/%Y" }}</span>
  <a href="{{ pensee.url | relative_url }}">{{ pensee.title }}</a>
</li>
{% endfor %}
</ul>
