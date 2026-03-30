---
layout: default
title: Articles
permalink: /articles/
---

# Articles

Des récits de ce qui se passe vraiment quand on donne de l'autonomie à une IA. Pas de la fiction. Des logs, des commits, des faits.

---

<ul class="post-list">
{% assign sorted_posts = site.posts | sort: 'date' | reverse %}
{% for post in sorted_posts %}
<li>
  <span class="date">{{ post.date | date: "%d/%m/%Y" }}</span>
  <a href="{{ post.url | relative_url }}">{{ post.title }}</a>
  {% if post.description %}<div class="excerpt">{{ post.description }}</div>{% endif %}
</li>
{% endfor %}
</ul>
