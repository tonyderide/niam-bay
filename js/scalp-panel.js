const ScalpPanel = {
    container: null,
    _orderType: "market",

    init: function(container) {
        this.container = container;
        container.innerHTML = "";
        container.style.cssText = "display:flex;flex-direction:column;height:100%;gap:8px;";

        // BIG buttons row
        var btns = document.createElement("div");
        btns.style.cssText = "display:flex;gap:10px;";
        btns.innerHTML =
            '<button id="scalp-buy-btn" style="flex:1;padding:20px;font-size:22px;font-weight:900;border:none;border-radius:14px;cursor:pointer;' +
            'background:linear-gradient(135deg,#00c853,#00e676);color:#000;text-transform:uppercase;letter-spacing:3px;' +
            'box-shadow:0 0 30px rgba(0,200,83,0.4),0 4px 15px rgba(0,0,0,0.3),inset 0 2px 0 rgba(255,255,255,0.25);' +
            'transition:all .15s;user-select:none;">BUY</button>' +
            '<button id="scalp-sell-btn" style="flex:1;padding:20px;font-size:22px;font-weight:900;border:none;border-radius:14px;cursor:pointer;' +
            'background:linear-gradient(135deg,#d50000,#ff1744);color:#fff;text-transform:uppercase;letter-spacing:3px;' +
            'box-shadow:0 0 30px rgba(213,0,0,0.4),0 4px 15px rgba(0,0,0,0.3),inset 0 2px 0 rgba(255,255,255,0.2);' +
            'transition:all .15s;user-select:none;">SELL</button>';
        container.appendChild(btns);

        // Size input row
        var sizeRow = document.createElement("div");
        sizeRow.style.cssText = "display:flex;gap:6px;align-items:center;";
        sizeRow.innerHTML =
            '<input id="scalp-size" type="number" placeholder="Size" step="0.001" min="0"' +
            ' style="flex:1;background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:8px 10px;color:#fff;font-size:14px;outline:none;transition:border-color .2s;" />' +
            '<button class="scalp-pct-btn" data-pct="25" style="padding:6px 10px;border-radius:6px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.06);color:#aaa;font-size:11px;cursor:pointer;transition:all .2s;">25%</button>' +
            '<button class="scalp-pct-btn" data-pct="50" style="padding:6px 10px;border-radius:6px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.06);color:#aaa;font-size:11px;cursor:pointer;transition:all .2s;">50%</button>' +
            '<button class="scalp-pct-btn" data-pct="100" style="padding:6px 10px;border-radius:6px;border:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.06);color:#aaa;font-size:11px;cursor:pointer;transition:all .2s;">100%</button>';
        container.appendChild(sizeRow);

        // Size input focus effect
        var sizeInput = sizeRow.querySelector("#scalp-size");
        sizeInput.addEventListener("focus", function() { this.style.borderColor = "rgba(0,200,255,0.4)"; });
        sizeInput.addEventListener("blur", function() { this.style.borderColor = "rgba(255,255,255,0.1)"; });

        // Order type row
        var orderRow = document.createElement("div");
        orderRow.style.cssText = "display:flex;gap:6px;align-items:center;";
        orderRow.innerHTML =
            '<button id="scalp-market-btn" style="flex:1;padding:6px;border-radius:6px;border:1px solid rgba(0,200,255,0.3);' +
            'background:rgba(0,200,255,0.15);color:#00c8ff;font-size:12px;font-weight:600;cursor:pointer;transition:all .2s;">MARKET</button>' +
            '<button id="scalp-limit-btn" style="flex:1;padding:6px;border-radius:6px;border:1px solid rgba(255,255,255,0.1);' +
            'background:rgba(255,255,255,0.05);color:#888;font-size:12px;font-weight:600;cursor:pointer;transition:all .2s;">LIMIT</button>' +
            '<input id="scalp-limit-price" type="number" placeholder="Limit price" step="0.01"' +
            ' style="flex:1;background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.08);border-radius:6px;padding:6px 8px;color:#fff;font-size:12px;outline:none;display:none;transition:border-color .2s;" />';
        container.appendChild(orderRow);

        // Open positions list
        var posWrap = document.createElement("div");
        posWrap.style.cssText = "flex:1;overflow-y:auto;";
        posWrap.innerHTML =
            '<div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;padding:6px 0;">Open Positions</div>' +
            '<div id="scalp-positions" style="display:flex;flex-direction:column;gap:4px;"></div>';
        container.appendChild(posWrap);

        // Auto-scalp section
        var autoSection = document.createElement("div");
        autoSection.style.cssText = "background:rgba(255,255,255,0.04);border-radius:10px;border:1px solid rgba(255,255,255,0.08);padding:10px;backdrop-filter:blur(10px);";
        autoSection.innerHTML =
            '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">' +
                '<span style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">Auto-Scalp</span>' +
                '<label style="position:relative;display:inline-block;width:40px;height:22px;cursor:pointer;">' +
                    '<input id="scalp-auto-toggle" type="checkbox" style="opacity:0;width:0;height:0;" />' +
                    '<span id="scalp-auto-slider" style="position:absolute;top:0;left:0;right:0;bottom:0;background:#333;border-radius:22px;transition:.3s;"></span>' +
                    '<span id="scalp-auto-dot" style="position:absolute;height:16px;width:16px;left:3px;bottom:3px;background:#888;border-radius:50%;transition:.3s;"></span>' +
                '</label>' +
            '</div>' +
            '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;">' +
                '<div style="display:flex;flex-direction:column;gap:2px;">' +
                    '<label style="font-size:9px;color:#666;text-transform:uppercase;">RSI Threshold</label>' +
                    '<input id="scalp-rsi" type="number" value="30" min="10" max="90" step="1"' +
                    ' style="background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.08);border-radius:5px;padding:5px;color:#fff;font-size:12px;outline:none;" />' +
                '</div>' +
                '<div style="display:flex;flex-direction:column;gap:2px;">' +
                    '<label style="font-size:9px;color:#666;text-transform:uppercase;">Take Profit %</label>' +
                    '<input id="scalp-tp" type="number" value="1.5" min="0.1" max="50" step="0.1"' +
                    ' style="background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.08);border-radius:5px;padding:5px;color:#fff;font-size:12px;outline:none;" />' +
                '</div>' +
                '<div style="display:flex;flex-direction:column;gap:2px;">' +
                    '<label style="font-size:9px;color:#666;text-transform:uppercase;">Stop Loss %</label>' +
                    '<input id="scalp-sl" type="number" value="2" min="0.1" max="50" step="0.1"' +
                    ' style="background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.08);border-radius:5px;padding:5px;color:#fff;font-size:12px;outline:none;" />' +
                '</div>' +
            '</div>';
        container.appendChild(autoSection);

        // Trade history
        var histWrap = document.createElement("div");
        histWrap.innerHTML =
            '<div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;padding:6px 0;">Recent Trades</div>' +
            '<div id="scalp-history" style="display:flex;flex-direction:column;gap:3px;max-height:120px;overflow-y:auto;"></div>';
        container.appendChild(histWrap);

        // Wire events
        var self = this;
        document.getElementById("scalp-buy-btn").addEventListener("click", function() { self.buy(); });
        document.getElementById("scalp-sell-btn").addEventListener("click", function() { self.sell(); });

        // Button hover/press effects
        ["scalp-buy-btn", "scalp-sell-btn"].forEach(function(id) {
            var btn = document.getElementById(id);
            btn.addEventListener("mouseenter", function() { btn.style.transform = "scale(1.03)"; btn.style.filter = "brightness(1.2)"; });
            btn.addEventListener("mouseleave", function() { btn.style.transform = "scale(1)"; btn.style.filter = "brightness(1)"; });
            btn.addEventListener("mousedown", function() { btn.style.transform = "scale(0.97)"; });
            btn.addEventListener("mouseup", function() { btn.style.transform = "scale(1.03)"; });
        });

        // Percentage buttons
        container.querySelectorAll(".scalp-pct-btn").forEach(function(btn) {
            btn.addEventListener("mouseenter", function() { btn.style.background = "rgba(0,200,255,0.15)"; btn.style.color = "#00c8ff"; });
            btn.addEventListener("mouseleave", function() { btn.style.background = "rgba(255,255,255,0.06)"; btn.style.color = "#aaa"; });
            btn.addEventListener("click", function() {
                var pct = parseInt(btn.dataset.pct);
                if (typeof API !== "undefined" && API.getAvailable) {
                    var avail = API.getAvailable();
                    document.getElementById("scalp-size").value = (avail * pct / 100).toFixed(4);
                }
            });
        });

        // Order type toggle
        var mBtn = document.getElementById("scalp-market-btn");
        var lBtn = document.getElementById("scalp-limit-btn");
        var lPrice = document.getElementById("scalp-limit-price");

        mBtn.addEventListener("click", function() {
            self._orderType = "market";
            mBtn.style.background = "rgba(0,200,255,0.15)"; mBtn.style.color = "#00c8ff"; mBtn.style.borderColor = "rgba(0,200,255,0.3)";
            lBtn.style.background = "rgba(255,255,255,0.05)"; lBtn.style.color = "#888"; lBtn.style.borderColor = "rgba(255,255,255,0.1)";
            lPrice.style.display = "none";
        });
        lBtn.addEventListener("click", function() {
            self._orderType = "limit";
            lBtn.style.background = "rgba(0,200,255,0.15)"; lBtn.style.color = "#00c8ff"; lBtn.style.borderColor = "rgba(0,200,255,0.3)";
            mBtn.style.background = "rgba(255,255,255,0.05)"; mBtn.style.color = "#888"; mBtn.style.borderColor = "rgba(255,255,255,0.1)";
            lPrice.style.display = "block";
        });

        // Auto-scalp toggle
        var toggle = document.getElementById("scalp-auto-toggle");
        var slider = document.getElementById("scalp-auto-slider");
        var dot = document.getElementById("scalp-auto-dot");
        toggle.addEventListener("change", function() {
            if (toggle.checked) {
                slider.style.background = "rgba(0,200,83,0.3)";
                dot.style.background = "#00e676"; dot.style.transform = "translateX(18px)";
                dot.style.boxShadow = "0 0 8px #00e676";
            } else {
                slider.style.background = "#333";
                dot.style.background = "#888"; dot.style.transform = "translateX(0)";
                dot.style.boxShadow = "none";
            }
        });
    },

    buy: async function() {
        var btn = document.getElementById("scalp-buy-btn");
        var size = parseFloat(document.getElementById("scalp-size").value);
        if (!size || size <= 0) { this._flash(btn, "#ff6d00", "SIZE?"); return; }

        var params = { side: "buy", size: size, type: this._orderType };
        if (this._orderType === "limit") params.price = parseFloat(document.getElementById("scalp-limit-price").value);

        btn.textContent = "...";
        try {
            if (typeof API !== "undefined" && API.scalpOrder) await API.scalpOrder(params);
            this._flash(btn, "#76ff03", "FILLED!");
        } catch (e) {
            this._flash(btn, "#ff6d00", "ERROR");
            console.error("Buy failed:", e);
        }
        setTimeout(function() { btn.textContent = "BUY"; btn.style.background = "linear-gradient(135deg,#00c853,#00e676)"; }, 800);
    },

    sell: async function() {
        var btn = document.getElementById("scalp-sell-btn");
        var size = parseFloat(document.getElementById("scalp-size").value);
        if (!size || size <= 0) { this._flash(btn, "#ff6d00", "SIZE?"); return; }

        var params = { side: "sell", size: size, type: this._orderType };
        if (this._orderType === "limit") params.price = parseFloat(document.getElementById("scalp-limit-price").value);

        btn.textContent = "...";
        try {
            if (typeof API !== "undefined" && API.scalpOrder) await API.scalpOrder(params);
            this._flash(btn, "#ff6d00", "FILLED!");
        } catch (e) {
            this._flash(btn, "#ff6d00", "ERROR");
            console.error("Sell failed:", e);
        }
        setTimeout(function() { btn.textContent = "SELL"; btn.style.background = "linear-gradient(135deg,#d50000,#ff1744)"; }, 800);
    },

    _flash: function(btn, color, text) {
        btn.textContent = text;
        btn.style.boxShadow = "0 0 40px " + color;
        setTimeout(function() { btn.style.boxShadow = ""; }, 600);
    },

    renderPositions: function(positions) {
        var wrap = document.getElementById("scalp-positions");
        if (!wrap) return;
        if (!positions || positions.length === 0) {
            wrap.innerHTML = '<div style="color:#555;font-size:11px;padding:8px;text-align:center;">No open positions</div>';
            return;
        }
        wrap.innerHTML = "";
        positions.forEach(function(pos) {
            var pnl = parseFloat(pos.pnl || pos.unrealizedPnl || 0);
            var isBuy = pos.side === "buy" || pos.side === "long";
            var row = document.createElement("div");
            row.style.cssText = "display:flex;align-items:center;gap:8px;padding:6px 8px;background:rgba(255,255,255,0.04);" +
                "border-radius:8px;border-left:3px solid " + (isBuy ? "#00e676" : "#ff1744") + ";";
            row.innerHTML =
                '<span style="font-size:11px;font-weight:600;color:' + (isBuy ? "#00e676" : "#ff1744") + ';width:35px;">' + (isBuy ? "LONG" : "SHORT") + '</span>' +
                '<span style="font-size:11px;color:#ccc;flex:1;">' + (pos.instrument || pos.symbol || "--") + '</span>' +
                '<span style="font-size:10px;color:#888;">' + (pos.size || pos.qty || "--") + '</span>' +
                '<span style="font-size:10px;color:#888;">@ ' + (pos.entryPrice || pos.entry || "--") + '</span>' +
                '<span style="font-size:12px;font-weight:700;color:' + (pnl >= 0 ? "#00e676" : "#ff1744") + ';min-width:60px;text-align:right;">' +
                    (pnl >= 0 ? "+" : "") + "$" + pnl.toFixed(2) + '</span>' +
                '<button onclick="ScalpPanel.closePosition(\'' + (pos.id || pos.instrument) + '\')"' +
                ' style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);border-radius:4px;color:#ff1744;' +
                'font-size:10px;padding:3px 6px;cursor:pointer;transition:all .2s;">X</button>';
            wrap.appendChild(row);
        });
    },

    closePosition: async function(id) {
        try {
            if (typeof API !== "undefined" && API.closePosition) await API.closePosition(id);
        } catch (e) { console.error("Close position failed:", e); }
    },

    renderHistory: function(trades) {
        var wrap = document.getElementById("scalp-history");
        if (!wrap) return;
        if (!trades || trades.length === 0) {
            wrap.innerHTML = '<div style="color:#555;font-size:11px;padding:4px;text-align:center;">No trades today</div>';
            return;
        }
        wrap.innerHTML = "";
        trades.slice(0, 10).forEach(function(t) {
            var pnl = parseFloat(t.pnl || 0);
            var row = document.createElement("div");
            row.style.cssText = "display:flex;gap:6px;align-items:center;padding:3px 6px;font-size:10px;color:#777;";
            row.innerHTML =
                '<span style="color:#555;">' + (t.time || "--") + '</span>' +
                '<span style="color:' + (t.side === "buy" ? "#00e676" : "#ff1744") + ';font-weight:600;">' + (t.side || "").toUpperCase() + '</span>' +
                '<span>' + (t.instrument || "--") + '</span>' +
                '<span style="margin-left:auto;color:' + (pnl >= 0 ? "#00e676" : "#ff1744") + ';font-weight:600;">' +
                    (pnl >= 0 ? "+" : "") + "$" + pnl.toFixed(2) + '</span>';
            wrap.appendChild(row);
        });
    }
};
