"""Minimal but selector-accurate HTML fixtures for mocked httpx responses."""

LISTING_PAGE_HTML: str = """<!DOCTYPE html>
<html>
<body>
  <span class="breadcrump-summary">1 - 25 von 3.006 Ergebnissen für „mini pc" in Deutschland</span>
  <article class="aditem" data-adid="12345678" data-href="/s-anzeige/test-item/12345678">
    <h2><a class="ellipsis" href="/s-anzeige/test-item/12345678">Test Item</a></h2>
    <p class="aditem-main--middle--price-shipping--price">149,99 €</p>
    <p class="aditem-main--middle--description">A nice test item in good condition</p>
  </article>
  <article class="aditem" data-adid="87654321" data-href="/s-anzeige/another-item/87654321">
    <h2><a class="ellipsis" href="/s-anzeige/another-item/87654321">Another Item VB</a></h2>
    <p class="aditem-main--middle--price-shipping--price">50 € VB</p>
    <p class="aditem-main--middle--description">Another item description</p>
  </article>
</body>
</html>"""

DETAIL_PAGE_HTML: str = """<!DOCTYPE html>
<html>
<body>
  <h1 id="viewad-title">Test Laptop</h1>
  <span id="viewad-price">299 € VB</span>
  <span id="viewad-locality">10115 Berlin - Mitte</span>
  <div id="viewad-description-text">Very good condition. Barely used.</div>
  <a class="breadcrump-link">Elektronik</a>
  <a class="breadcrump-link">Laptops</a>
  <img id="viewad-image" src="https://img.kleinanzeigen.de/test1.jpg" />
  <img id="viewad-image" src="https://img.kleinanzeigen.de/test2.jpg" />
  <div class="boxedarticle--details--shipping">Versand möglich (4,99 €)</div>
  <div id="viewad-details">
    <dl class="addetailslist--detail"><dt>Zustand</dt><dd>Gebraucht</dd></dl>
    <dl class="addetailslist--detail"><dt>Marke</dt><dd>Dell</dd></dl>
  </div>
  <div id="viewad-configuration">
    <span class="checktag">Feature 1</span>
    <span class="checktag">Feature 2</span>
  </div>
  <div id="viewad-extra-info"><span>Gestern, 14:32</span></div>
  <div class="userprofile-vip">max_user</div>
  <div class="userprofile-vip-details-text">Aktiv seit 2020</div>
</body>
</html>"""

DETAIL_PAGE_BUSINESS_HTML: str = """<!DOCTYPE html>
<html>
<body>
  <h1 id="viewad-title">Business Laptop</h1>
  <span id="viewad-price">999 €</span>
  <span id="viewad-locality">80331 München</span>
  <div class="userprofile-vip">TechShop GmbH</div>
  <div class="userprofile-vip-details-text">Gewerblicher Anbieter</div>
  <div class="userprofile-vip-details-text">Aktiv seit 2018</div>
</body>
</html>"""

EMPTY_LISTING_PAGE_HTML: str = """<!DOCTYPE html>
<html>
<body>
  <span class="breadcrump-summary">Keine Ergebnisse</span>
</body>
</html>"""

IP_BAN_HTML: str = """<!DOCTYPE html>
<html>
<body>
  <h1>IP-Bereich vorübergehend gesperrt</h1>
  <p>Ihr IP-Bereich wurde vorübergehend gesperrt.</p>
</body>
</html>"""
