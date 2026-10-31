/* Imported Bites, shared app.js */
/* ============================================================
   CONFIG: WhatsApp number for all order links.
   Owner-supplied number (2026-10-31): 0337 3698048.
   wa.me format below (country code + number, no plus, no spaces).
   ============================================================ */
var WHATSAPP_NUMBER = "923373698048";

/* Order email notifications (free FormSubmit service).
   Set to the owner's inbox to also email every order. WhatsApp stays the primary channel. */
var ORDER_EMAIL = "ORDERS_EMAIL_PLACEHOLDER";

/* Product catalog mirror, synced by build.py from data/products.json.
   Currently empty: the confirmed product list is pending from the owner. */
var PRODUCTS = /*__PRODUCTS__*/ {"me-o-adult-tuna-1-1kg": {"name": "Me-O Adult Tuna 1.1kg (Thailand)", "price": 2000, "emoji": "🐱", "stock": 24, "img": "/assets/img/products/meo-adult-tuna.png"}, "me-o-persian-anti-hairball-1-1kg": {"name": "Me-O Persian Adult Anti Hairball 1.1kg", "price": 2200, "emoji": "🐱", "stock": 15, "img": "/assets/img/products/meo-persian-hairball.jpg"}, "me-o-kitten-1-1kg": {"name": "Me-O Kitten 1.1kg", "price": 2100, "emoji": "🐱", "stock": 18, "img": "/assets/img/products/meo-kitten.jpg"}, "me-o-mother-baby-cat-1-1kg": {"name": "Me-O Mother and Baby Cat 1.1kg", "price": 2000, "emoji": "🐱", "stock": 12, "img": "/assets/img/products/meo-mother-baby.jpg"}, "whiskas-adult-chicken-1-9kg": {"name": "Whiskas Adult Chicken 1.9kg", "price": 4800, "emoji": "🐱", "stock": 10, "img": "/assets/img/products/whiskas-adult-chicken-1-9kg.jpg"}, "whiskas-kitten-chicken-1-9kg": {"name": "Whiskas Kitten Chicken 1.9kg", "price": 5000, "emoji": "🐱", "stock": 8, "img": "/assets/img/products/whiskas-kitten-chicken-1-9kg.jpg"}, "whiskas-junior-1-1kg": {"name": "Whiskas Junior 1.1kg", "price": 2499, "emoji": "🐱", "stock": 20, "img": "/assets/img/products/whiskas-junior-1-1kg.jpg"}, "whiskas-pouch-beef-poultry-85g": {"name": "Whiskas Pouch Beef and Poultry 85g", "price": 240, "emoji": "🥫", "stock": 48, "img": "/assets/img/products/whiskas-pouch-beef-poultry-85g.png"}, "whiskas-pouches-12x85g-jelly-variety": {"name": "Whiskas Pouches 12x85g Jelly Variety Pack", "price": 2950, "emoji": "🥫", "stock": 14, "img": "/assets/img/products/whiskas-pouches-12x85g.jpg"}, "whiskas-meaty-meals-jelly-85g": {"name": "Whiskas Meaty Meals in Jelly 85g", "price": 250, "emoji": "🥫", "stock": 36, "img": "/assets/img/products/whiskas-meaty-meals-jelly-85g.jpg"}, "whiskas-temptations-chicken-45g": {"name": "Whiskas Temptations Chicken Treats 45g", "price": 600, "emoji": "🦴", "stock": 22, "img": "/assets/img/products/whiskas-temptations-chicken-45g.webp"}, "me-o-creamy-treats-tuna": {"name": "Me-O Creamy Treats Tuna Pack", "price": 650, "emoji": "🦴", "stock": 16, "img": "/assets/img/products/meo-creamy-treats.webp"}, "temptations-creamy-puree-salmon-4pack": {"name": "Temptations Creamy Puree Salmon 4 Pack", "price": 1200, "emoji": "🦴", "stock": 9, "img": "/assets/img/products/temptations-creamy-puree-salmon.jpg"}, "klumpy-bentonite-litter-5l-lavender": {"name": "Klumpy Bentonite Cat Litter 5L Lavender", "price": 650, "emoji": "🧹", "stock": 30, "img": "/assets/img/products/klumpy-cat-litter-5l.jpg"}, "premium-bentonite-litter-10l-lavender": {"name": "Premium Bentonite Cat Litter 10L Lavender", "price": 1600, "emoji": "🧹", "stock": 12, "img": ""}, "easy-clean-emily-pets-litter-10l": {"name": "Easy Clean Emily Pets Cat Litter 10L Imported", "price": 1400, "emoji": "🧹", "stock": 18, "img": ""}, "bentonite-litter-10l-coffee": {"name": "Bentonite Cat Litter 10L Coffee Scent", "price": 1500, "emoji": "🧹", "stock": 11, "img": ""}, "nescafe-gold-200g": {"name": "Nescafe Gold 200g", "price": 3200, "emoji": "☕", "stock": 9, "img": ""}, "stevia-sweetener": {"name": "Stevia Sweetener", "price": 950, "emoji": "🌿", "stock": 25, "img": "/assets/img/products/stevia-powder.png"}, "haribo-goldbears-200g": {"name": "Haribo Goldbears 200g", "price": 950, "emoji": "🐻", "stock": 26, "img": "/assets/img/products/haribo-goldbears-200g.jpg"}};

function fmtPKR(n) {
  return "PKR " + n.toLocaleString("en-US");
}
function waLink(message) {
  return "https://wa.me/" + WHATSAPP_NUMBER + "?text=" + encodeURIComponent(message);
}

/* ---------- Cart ---------- */
var CART_KEY = "ib_cart";
function getCart() {
  try {
    var c = JSON.parse(localStorage.getItem(CART_KEY) || "{}");
    return (c && typeof c === "object") ? c : {};
  } catch (e) { return {}; }
}
function saveCart(c) { localStorage.setItem(CART_KEY, JSON.stringify(c)); }
function cartCount() {
  var c = getCart(), n = 0;
  Object.keys(c).forEach(function (k) { n += c[k]; });
  return n;
}
function addToCart(slug, qty) {
  var p = PRODUCTS[slug];
  if (!p) return;
  if (p.stock <= 0) { alert("Sorry, this item is out of stock right now. WhatsApp us to pre-order."); return; }
  var c = getCart();
  var next = (c[slug] || 0) + (qty || 1);
  if (next > p.stock) { alert("Only " + p.stock + " in stock. We added what is available."); next = p.stock; }
  c[slug] = next;
  saveCart(c);
  renderCart();
  openCart();
}
function cartTotal() {
  var c = getCart(), t = 0;
  Object.keys(c).forEach(function (k) { if (PRODUCTS[k]) t += PRODUCTS[k].price * c[k]; });
  return t;
}
function renderCart() {
  var badge = document.getElementById("cart-count");
  if (badge) badge.textContent = cartCount();
  var box = document.getElementById("cart-items");
  if (!box) return;
  var c = getCart();
  var keys = Object.keys(c).filter(function (k) { return PRODUCTS[k] && c[k] > 0; });
  if (keys.length === 0) {
    box.innerHTML = '<p class="cart-empty">Your cart is empty.<br>Add some imported goodies to get started.</p>';
  } else {
    var html = "";
    keys.forEach(function (k) {
      var p = PRODUCTS[k];
      var thumb = p.img
        ? '<img class="ci-img" src="' + p.img + '" alt="">'
        : p.emoji;
      html += '<div class="cart-item">' +
        '<span class="ci-emoji">' + thumb + '</span>' +
        '<div class="ci-info"><strong>' + p.name + '</strong>' +
        '<span>' + fmtPKR(p.price) + '</span>' +
        '<div class="qty-row">' +
        '<button class="qty-btn" data-act="dec" data-slug="' + k + '" type="button">-</button>' +
        '<strong>' + c[k] + '</strong>' +
        '<button class="qty-btn" data-act="inc" data-slug="' + k + '" type="button">+</button>' +
        '<button class="ci-remove" data-act="rm" data-slug="' + k + '" type="button">Remove</button>' +
        '</div></div></div>';
    });
    box.innerHTML = html;
  }
  var totalEl = document.getElementById("cart-total");
  if (totalEl) totalEl.textContent = fmtPKR(cartTotal());
  var hint = document.getElementById("free-delivery-hint");
  if (hint) {
    var sub = cartTotal();
    if (sub <= 0) {
      hint.className = "free-delivery-hint";
      hint.textContent = "";
    } else if (sub < 3000) {
      hint.className = "free-delivery-hint show progress";
      hint.textContent = "Add Rs " + (3000 - sub).toLocaleString("en-US") + " more for FREE Karachi delivery";
    } else {
      hint.className = "free-delivery-hint show unlocked";
      hint.textContent = "🎉 FREE Karachi Delivery Unlocked";
    }
  }
  var foot = document.getElementById("cart-foot");
  if (foot) foot.style.display = keys.length ? "" : "none";
}
function openCart() {
  var d = document.getElementById("cart-drawer"), o = document.getElementById("cart-overlay");
  if (d) d.classList.add("open");
  if (o) o.classList.add("open");
  document.body.style.overflow = "hidden";
  renderCart();
}
function closeCart() {
  var d = document.getElementById("cart-drawer"), o = document.getElementById("cart-overlay");
  if (d) d.classList.remove("open");
  if (o) o.classList.remove("open");
  document.body.style.overflow = "";
}

/* ---------- WhatsApp order links ---------- */
function orderSingleProduct(slug) {
  var p = PRODUCTS[slug];
  if (!p) return;
  var msg = "Hi Imported Bites! I want to order (Cash on Delivery):\n" +
    p.name + " x1 = " + fmtPKR(p.price) + "\nTotal: " + fmtPKR(p.price) +
    "\n\nPlease confirm availability. Thank you!";
  window.open(waLink(msg), "_blank");
}
function emailOrder(lines) {
  if (!ORDER_EMAIL || ORDER_EMAIL.indexOf("@") < 0 || ORDER_EMAIL.indexOf("PLACEHOLDER") >= 0) return;
  try {
    fetch("https://formsubmit.co/ajax/" + ORDER_EMAIL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({
        _subject: "New order, Imported Bites, " + fmtPKR(cartTotal()),
        _template: "table",
        message: lines.join("\n")
      })
    }).catch(function () {});
  } catch (e) {}
}
function placeWhatsAppOrder() {
  var name = document.getElementById("co-name").value.trim();
  var phone = document.getElementById("co-phone").value.trim();
  var address = document.getElementById("co-address").value.trim();
  var city = document.getElementById("co-city").value.trim();
  if (!name || !phone || !address || !city) {
    alert("Please fill in your name, phone, address and city so we can deliver your order.");
    return;
  }
  var c = getCart();
  var keys = Object.keys(c).filter(function (k) { return PRODUCTS[k] && c[k] > 0; });
  if (keys.length === 0) { alert("Your cart is empty."); return; }
  var lines = ["New order from the Imported Bites website (Cash on Delivery):", ""];
  var i = 1;
  keys.forEach(function (k) {
    var p = PRODUCTS[k];
    lines.push(i + ") " + p.name + " x" + c[k] + " = " + fmtPKR(p.price * c[k]));
    i++;
  });
  var subtotal = cartTotal();
  var deliveryLine = subtotal >= 3000
    ? "Delivery: FREE (Karachi order over Rs 3,000)"
    : "Delivery: calculated at confirmation";
  lines.push("", "Total: " + fmtPKR(subtotal), deliveryLine, "",
    "Name: " + name, "Phone: " + phone, "Address: " + address, "City: " + city,
    "", "Please confirm my order. Thank you!");
  emailOrder(lines);
  window.open(waLink(lines.join("\n")), "_blank");
}

/* ---------- Shop filters ---------- */
function applyShopFilters() {
  var grid = document.getElementById("product-grid");
  if (!grid) return;
  var activeBtn = document.querySelector(".filter-btn.active");
  var cat = activeBtn ? activeBtn.getAttribute("data-cat") : "all";
  var q = document.getElementById("shop-search-input");
  var term = q ? q.value.trim().toLowerCase() : "";
  var cards = grid.querySelectorAll(".card");
  var visible = 0;
  cards.forEach(function (card) {
    var okCat = (cat === "all" || card.getAttribute("data-category") === cat);
    var okTerm = (!term || card.getAttribute("data-name").toLowerCase().indexOf(term) !== -1);
    var show = okCat && okTerm;
    card.style.display = show ? "" : "none";
    if (show) visible++;
  });
  var none = document.getElementById("no-results");
  if (none) none.style.display = visible ? "none" : "";
}

/* ---------- Init ---------- */
document.addEventListener("DOMContentLoaded", function () {
  renderCart();

  document.querySelectorAll("[data-cart-open]").forEach(function (el) {
    el.addEventListener("click", openCart);
  });
  var closeBtn = document.getElementById("cart-close");
  if (closeBtn) closeBtn.addEventListener("click", closeCart);
  var overlay = document.getElementById("cart-overlay");
  if (overlay) overlay.addEventListener("click", closeCart);

  document.addEventListener("click", function (e) {
    var t = e.target;
    if (t.matches("[data-add-cart]")) { addToCart(t.getAttribute("data-add-cart")); return; }
    if (t.matches("[data-wa-order]")) { orderSingleProduct(t.getAttribute("data-wa-order")); return; }
    var qbtn = t.closest ? t.closest("[data-act]") : null;
    if (qbtn) {
      var slug = qbtn.getAttribute("data-slug"), act = qbtn.getAttribute("data-act");
      var c = getCart();
      if (act === "inc") { if (c[slug] < PRODUCTS[slug].stock) c[slug]++; }
      if (act === "dec") { c[slug]--; if (c[slug] <= 0) delete c[slug]; }
      if (act === "rm") { delete c[slug]; }
      saveCart(c); renderCart(); return;
    }
  });

  var coBtn = document.getElementById("checkout-toggle");
  if (coBtn) coBtn.addEventListener("click", function () {
    var form = document.getElementById("checkout-form");
    form.classList.toggle("show");
    if (form.classList.contains("show")) {
      setTimeout(function () {
        var scroller = document.querySelector(".cart-scroll");
        if (scroller) scroller.scrollTop = scroller.scrollHeight;
        else form.scrollIntoView({ block: "end" });
      }, 60);
    }
  });
  var placeBtn = document.getElementById("place-order-btn");
  if (placeBtn) placeBtn.addEventListener("click", placeWhatsAppOrder);

  var burger = document.getElementById("hamburger");
  if (burger) burger.addEventListener("click", function () {
    document.getElementById("main-nav").classList.toggle("open");
  });

  var hSearch = document.getElementById("header-search");
  if (hSearch) hSearch.addEventListener("submit", function (e) {
    e.preventDefault();
    var v = document.getElementById("header-search-input").value.trim();
    window.location.href = "/shop.html" + (v ? "?q=" + encodeURIComponent(v) : "");
  });

  document.querySelectorAll(".filter-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".filter-btn").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      applyShopFilters();
    });
  });
  var sInput = document.getElementById("shop-search-input");
  if (sInput) {
    var params = new URLSearchParams(window.location.search);
    var preset = params.get("q");
    if (preset) sInput.value = preset;
    sInput.addEventListener("input", applyShopFilters);
    applyShopFilters();
  }

  document.querySelectorAll(".faq-list").forEach(function (list) {
    list.querySelectorAll("details").forEach(function (d) {
      d.addEventListener("toggle", function () {
        if (d.open) {
          list.querySelectorAll("details").forEach(function (o) { if (o !== d) o.open = false; });
        }
      });
    });
  });
});

/* Hero slider */
document.addEventListener("DOMContentLoaded", function () {
  var box = document.getElementById("hero-slides");
  if (!box) return;
  var slides = Array.prototype.slice.call(box.querySelectorAll(".slide"));
  var dots = Array.prototype.slice.call(document.querySelectorAll(".slide-dot"));
  var prev = document.querySelector("[data-slide-prev]");
  var next = document.querySelector("[data-slide-next]");
  var i = 0, timer = null;
  function go(n) {
    i = (n + slides.length) % slides.length;
    slides.forEach(function (s, k) { s.classList.toggle("active", k === i); });
    dots.forEach(function (d, k) { d.classList.toggle("active", k === i); });
  }
  function auto() { timer = setInterval(function () { go(i + 1); }, 3000); }
  function reset() { if (timer) clearInterval(timer); auto(); }
  if (prev) prev.addEventListener("click", function () { go(i - 1); reset(); });
  if (next) next.addEventListener("click", function () { go(i + 1); reset(); });
  dots.forEach(function (d) {
    d.addEventListener("click", function () { go(parseInt(d.getAttribute("data-slide"), 10)); reset(); });
  });
  var slider = document.querySelector(".hero-slider");
  var canHover = window.matchMedia && window.matchMedia("(hover: hover)").matches;
  if (slider && canHover) {
    slider.addEventListener("mouseenter", function () { if (timer) clearInterval(timer); timer = null; });
    slider.addEventListener("mouseleave", function () { if (!timer) auto(); });
  }
  auto();
});

/* Sticky mobile add-to-cart on product pages */
document.addEventListener("DOMContentLoaded", function () {
  var bar = document.getElementById("sticky-atc");
  if (!bar) return;
  var actions = document.querySelector(".product-actions");
  var ticking = false;
  function update() {
    ticking = false;
    if (!actions) { bar.classList.remove("show"); return; }
    var rect = actions.getBoundingClientRect();
    var past = rect.bottom < 0;
    var atBottom = window.innerHeight + window.scrollY > document.documentElement.scrollHeight - 120;
    bar.classList.toggle("show", past && !atBottom);
  }
  window.addEventListener("scroll", function () {
    if (!ticking) { ticking = true; requestAnimationFrame(update); }
  }, { passive: true });
  update();
});

/* Back-to-top button (footer) */
document.addEventListener("DOMContentLoaded", function () {
  var btn = document.getElementById("to-top");
  if (!btn) return;
  var ticking = false;
  function update() {
    ticking = false;
    btn.classList.toggle("show", window.scrollY > 600);
  }
  window.addEventListener("scroll", function () {
    if (!ticking) { ticking = true; requestAnimationFrame(update); }
  }, { passive: true });
  btn.addEventListener("click", function () {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  update();
});
