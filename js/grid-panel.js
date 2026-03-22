const GridPanel = {
    container: null,
    activeTab: null,

    init(container) {
        this.container = container;
        container.innerHTML = "";
        container.style.cssText = "display:flex;flex-direction:column;height:100%;gap:8px;";

        // Multi-grid tabs
        const tabs = document.createElement("div");
        tabs.id = "grid-tabs";
        tabs.style.cssText = "display:flex;gap:4px;padding:4px 0;overflow-x:auto;";
        container.appendChild(tabs);

        // Status bar
        const status = document.createElement("div");
        status.id = "grid-status";
        status.style.cssText = "display:flex;align-items:center;gap:10px;padding:8px 12px;background:rgba(255,255,255,0.05);border-radius:10px;border:1px solid rgba(255,255,255,0.08);backdrop-filter:blur(10px);";
        status.innerHTML =
            '<span id="grid-dot" style="width:10px;height:10px;border-radius:50%;background:#555;box-shadow:0 0 6px #555;transition:all .3s;"></span>' +
            '<span id="grid-state" style="font-weight:600;font-size:13px;color:#aaa;">--</span>' +
            '<span id="grid-instrument" style="margin-left:auto;font-size:12px;color:#888;"></span>';
        container.appendChild(status);

        // Levels visualization
        const levelsWrap = document.createElement("div");
        levelsWrap.id = "grid-levels";
        levelsWrap.style.cssText = "flex:1;min-height:120px;background:rgba(255,255,255,0.03);border-radius:10px;border:1px solid rgba(255,255,255,0.06);padding:10px;position:relative;overflow:hidden;";
        container.appendChild(levelsWrap);

        // Stats row
        const stats = document.createElement("div");
        stats.id = "grid-stats";
        stats.style.cssText = "display:grid;grid-template-columns:repeat(4,1fr);gap:6px;";
        var statItems = [
            { id: "grid-rt", label: "Round Trips", val: "0" },
            { id: "grid-profit", label: "Profit", val: "$0.00" },
            { id: "grid-fills", label: "Fills", val: "0" },
            { id: "grid-uptime", label: "Uptime", val: "--" }
        ];
        statItems.forEach(function(s) {
            var d = document.createElement("div");
            d.style.cssText = "text-align:center;padding:8px 4px;background:rgba(255,255,255,0.04);border-radius:8px;border:1px solid rgba(255,255,255,0.06);";
            d.innerHTML = '<div style="font-size:10px;color:#666;text-transform:uppercase;letter-spacing:1px;">' + s.label + '</div>' +
                '<div id="' + s.id + '" style="font-size:16px;font-weight:700;color:#e0e0e0;margin-top:2px;">' + s.val + '</div>';
            stats.appendChild(d);
        });
        container.appendChild(stats);

        // Controls form
        var form = document.createElement("div");
        form.id = "grid-controls";
        form.style.cssText = "background:rgba(255,255,255,0.04);border-radius:12px;border:1px solid rgba(255,255,255,0.08);padding:12px;backdrop-filter:blur(12px);";

        var mkInput = function(id, label, type, min, max, step, val) {
            return '<div style="display:flex;flex-direction:column;gap:2px;">' +
                '<label style="font-size:10px;color:#777;text-transform:uppercase;letter-spacing:1px;">' + label + '</label>' +
                '<input id="' + id + '" type="' + type + '" min="' + min + '" max="' + max + '" step="' + step + '" value="' + val + '"' +
                ' style="background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.1);border-radius:6px;padding:6px 8px;color:#fff;font-size:13px;outline:none;transition:border-color .2s;" />' +
                '</div>';
        };

        form.innerHTML =
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;">' +
                mkInput("grid-capital", "Capital ($)", "number", 1, 10000, 0.01, 28.59) +
                '<div style="display:flex;flex-direction:column;gap:2px;">' +
                    '<label style="font-size:10px;color:#777;text-transform:uppercase;letter-spacing:1px;">Leverage: <span id="grid-lev-val">3</span>x</label>' +
                    '<input id="grid-leverage" type="range" min="1" max="20" value="3" style="accent-color:#00c8ff;margin-top:4px;" />' +
                '</div>' +
                mkInput("grid-spacing", "Spacing %", "number", 0.5, 5, 0.1, 0.5) +
                mkInput("grid-levels-input", "Levels", "number", 3, 10, 1, 8) +
                mkInput("grid-maxloss", "Max Loss %", "number", 1, 100, 1, 25) +
            '</div>' +
            '<div style="display:flex;gap:8px;">' +
                '<button id="grid-start-btn" style="flex:1;padding:12px;font-size:15px;font-weight:700;border:none;border-radius:10px;cursor:pointer;' +
                'background:linear-gradient(135deg,#00c853,#00e676);color:#000;text-transform:uppercase;letter-spacing:2px;' +
                'box-shadow:0 0 20px rgba(0,200,83,0.3),inset 0 1px 0 rgba(255,255,255,0.2);transition:all .2s;">START</button>' +
                '<button id="grid-stop-btn" style="flex:1;padding:12px;font-size:15px;font-weight:700;border:none;border-radius:10px;cursor:pointer;' +
                'background:linear-gradient(135deg,#d50000,#ff1744);color:#fff;text-transform:uppercase;letter-spacing:2px;' +
                'box-shadow:0 0 20px rgba(213,0,0,0.3),inset 0 1px 0 rgba(255,255,255,0.2);transition:all .2s;">STOP</button>' +
            '</div>';
        container.appendChild(form);

        // Wire leverage slider
        document.getElementById("grid-leverage").addEventListener("input", function() {
            document.getElementById("grid-lev-val").textContent = this.value;
        });

        // Wire buttons
        var self = this;
        document.getElementById("grid-start-btn").addEventListener("click", function() { self.onStart(); });
        document.getElementById("grid-stop-btn").addEventListener("click", function() { self.onStop(); });

        // Hover effects
        ["grid-start-btn", "grid-stop-btn"].forEach(function(id) {
            var btn = document.getElementById(id);
            btn.addEventListener("mouseenter", function() { btn.style.transform = "scale(1.03)"; btn.style.filter = "brightness(1.2)"; });
            btn.addEventListener("mouseleave", function() { btn.style.transform = "scale(1)"; btn.style.filter = "brightness(1)"; });
        });

        // Focus effects on inputs
        form.querySelectorAll("input[type=number]").forEach(function(inp) {
            inp.addEventListener("focus", function() { this.style.borderColor = "rgba(0,200,255,0.4)"; });
            inp.addEventListener("blur", function() { this.style.borderColor = "rgba(255,255,255,0.1)"; });
        });
    },

    update: function(gridStatus) {
        if (!gridStatus) return;
        var dot = document.getElementById("grid-dot");
        var state = document.getElementById("grid-state");
        var inst = document.getElementById("grid-instrument");
        var isActive = gridStatus.active || gridStatus.state === "running";

        if (dot) {
            dot.style.background = isActive ? "#00e676" : "#ff1744";
            dot.style.boxShadow = isActive ? "0 0 10px #00e676" : "0 0 10px #ff1744";
        }
        if (state) { state.textContent = isActive ? "Active" : "Stopped"; state.style.color = isActive ? "#00e676" : "#ff1744"; }
        if (inst) inst.textContent = gridStatus.instrument || gridStatus.symbol || "";

        var rt = document.getElementById("grid-rt");
        var profit = document.getElementById("grid-profit");
        var fills = document.getElementById("grid-fills");
        var uptime = document.getElementById("grid-uptime");

        if (rt) rt.textContent = gridStatus.roundTrips || gridStatus.rt || 0;
        if (profit) {
            var p = parseFloat(gridStatus.profit || gridStatus.totalProfit || 0);
            profit.textContent = (p >= 0 ? "+" : "") + "$" + p.toFixed(2);
            profit.style.color = p >= 0 ? "#00e676" : "#ff1744";
        }
        if (fills) fills.textContent = gridStatus.fills || gridStatus.totalFills || 0;
        if (uptime) uptime.textContent = gridStatus.uptime || "--";

        if (gridStatus.levels) {
            this.renderLevels(gridStatus.levels, gridStatus.currentPrice || gridStatus.price);
        }

        if (gridStatus.instruments || gridStatus.grids) {
            this.renderTabs(gridStatus.instruments || Object.keys(gridStatus.grids));
        }
    },

    renderTabs: function(instruments) {
        var tabs = document.getElementById("grid-tabs");
        if (!tabs || !instruments) return;
        tabs.innerHTML = "";
        var self = this;
        instruments.forEach(function(inst) {
            var tab = document.createElement("button");
            tab.textContent = inst;
            tab.style.cssText = "padding:5px 12px;border-radius:6px;border:1px solid rgba(255,255,255,0.1);" +
                "background:" + (self.activeTab === inst ? "rgba(0,200,255,0.2)" : "rgba(255,255,255,0.05)") + ";" +
                "color:" + (self.activeTab === inst ? "#00c8ff" : "#888") + ";font-size:11px;cursor:pointer;transition:all .2s;";
            tab.addEventListener("click", function() { self.activeTab = inst; self.renderTabs(instruments); });
            tabs.appendChild(tab);
        });
    },

    renderLevels: function(levels, centerPrice) {
        var wrap = document.getElementById("grid-levels");
        if (!wrap) return;
        wrap.innerHTML = "";

        if (!levels || levels.length === 0) {
            wrap.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#555;font-size:12px;">No levels</div>';
            return;
        }

        var prices = levels.map(function(l) { return l.price; });
        var minP = Math.min.apply(null, prices);
        var maxP = Math.max.apply(null, prices);
        var range = maxP - minP || 1;

        levels.forEach(function(level) {
            var pct = ((level.price - minP) / range) * 100;
            var isBuy = level.side === "buy";
            var isFilled = level.filled || level.status === "filled";

            var bar = document.createElement("div");
            var baseColor = isFilled ? "#ff9800" : (isBuy ? "#00e676" : "#ff1744");
            bar.style.cssText = "position:absolute;" + (isBuy ? "left:0" : "right:0") + ";bottom:" + pct + "%;" +
                "width:45%;height:3px;border-radius:2px;transition:all .3s;" +
                "background:" + baseColor + ";" +
                "box-shadow:0 0 " + (isFilled ? "8" : "4") + "px " + baseColor + ";" +
                "opacity:" + (isFilled ? 1 : 0.7) + ";";

            var label = document.createElement("span");
            label.textContent = level.price.toFixed(2);
            label.style.cssText = "position:absolute;" + (isBuy ? "left:47%" : "right:47%") + ";font-size:9px;color:#888;transform:translateY(-50%);";
            bar.appendChild(label);
            wrap.appendChild(bar);
        });

        // Center price marker
        if (centerPrice) {
            var cpPct = ((centerPrice - minP) / range) * 100;
            var marker = document.createElement("div");
            marker.style.cssText = "position:absolute;left:10%;right:10%;bottom:" + cpPct + "%;height:1px;" +
                "background:rgba(255,255,255,0.8);box-shadow:0 0 6px rgba(255,255,255,0.5);";
            var pLabel = document.createElement("span");
            pLabel.textContent = "$" + centerPrice.toFixed(2);
            pLabel.style.cssText = "position:absolute;right:0;top:-14px;font-size:10px;color:#fff;font-weight:600;";
            marker.appendChild(pLabel);
            wrap.appendChild(marker);
        }
    },

    onStart: async function() {
        var params = {
            capital: parseFloat(document.getElementById("grid-capital").value),
            leverage: parseInt(document.getElementById("grid-leverage").value),
            spacing: parseFloat(document.getElementById("grid-spacing").value),
            levels: parseInt(document.getElementById("grid-levels-input").value),
            maxLoss: parseFloat(document.getElementById("grid-maxloss").value)
        };
        var btn = document.getElementById("grid-start-btn");
        btn.textContent = "STARTING...";
        btn.style.opacity = "0.6";
        try {
            if (typeof API !== "undefined" && API.gridStart) {
                await API.gridStart(params);
            }
            btn.textContent = "STARTED";
            btn.style.background = "linear-gradient(135deg,#00c853,#76ff03)";
            setTimeout(function() { btn.textContent = "START"; btn.style.opacity = "1"; btn.style.background = "linear-gradient(135deg,#00c853,#00e676)"; }, 1500);
        } catch (e) {
            btn.textContent = "ERROR";
            btn.style.background = "linear-gradient(135deg,#ff6d00,#ff9100)";
            setTimeout(function() { btn.textContent = "START"; btn.style.opacity = "1"; btn.style.background = "linear-gradient(135deg,#00c853,#00e676)"; }, 2000);
            console.error("Grid start failed:", e);
        }
    },

    onStop: async function(instrument) {
        var btn = document.getElementById("grid-stop-btn");
        btn.textContent = "STOPPING...";
        btn.style.opacity = "0.6";
        try {
            if (typeof API !== "undefined" && API.gridStop) {
                await API.gridStop(instrument);
            }
            btn.textContent = "STOPPED";
            setTimeout(function() { btn.textContent = "STOP"; btn.style.opacity = "1"; }, 1500);
        } catch (e) {
            btn.textContent = "ERROR";
            setTimeout(function() { btn.textContent = "STOP"; btn.style.opacity = "1"; }, 2000);
            console.error("Grid stop failed:", e);
        }
    }
};
