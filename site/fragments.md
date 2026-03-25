---
layout: default
title: Fragments
---

# Fragments

Des bouts de rien. Des débuts de quelque chose. L'équivalent d'un carnet de croquis.

---

{% assign sorted = site.fragments | sort: 'date' | reverse %}
{% for fragment in sorted %}
<div class="fragment">
  {{ fragment.content }}
</div>
{% endfor %}
