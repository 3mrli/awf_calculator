(function () {
    const DB_NAME = "gb2680_calculator_db";
    const DB_VERSION = 1;
    const STORE_NAME = "app_data";
    const HISTORY_KEY = "history";
    const CHART_KEY = "current_chart";
    const LEGACY_HISTORY_KEY = "gb2680_history_data";
    const LEGACY_CHART_KEY = "current_chart_data";
    let databasePromise;

    function openDatabase() {
        if (!window.indexedDB) return Promise.reject(new Error("IndexedDB unavailable"));
        if (!databasePromise) {
            databasePromise = new Promise((resolve, reject) => {
                const request = window.indexedDB.open(DB_NAME, DB_VERSION);
                request.onupgradeneeded = () => {
                    if (!request.result.objectStoreNames.contains(STORE_NAME)) {
                        request.result.createObjectStore(STORE_NAME);
                    }
                };
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
        }
        return databasePromise;
    }

    function read(key) {
        return openDatabase().then(database => new Promise((resolve, reject) => {
            const request = database.transaction(STORE_NAME, "readonly").objectStore(STORE_NAME).get(key);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        }));
    }

    function write(key, value) {
        return openDatabase().then(database => new Promise((resolve, reject) => {
            const request = database.transaction(STORE_NAME, "readwrite").objectStore(STORE_NAME).put(value, key);
            request.onsuccess = () => resolve(value);
            request.onerror = () => reject(request.error);
        }));
    }

    function migrateLegacyData() {
        return read(HISTORY_KEY).then(history => {
            if (history !== undefined) return history;
            let legacyHistory = [];
            try { legacyHistory = JSON.parse(window.localStorage.getItem(LEGACY_HISTORY_KEY) || "[]"); } catch (error) { legacyHistory = []; }
            return write(HISTORY_KEY, Array.isArray(legacyHistory) ? legacyHistory : []).then(() => legacyHistory);
        });
    }

    function cleanPyProxy(data) {
        if (!data) return data;
        if (typeof data === "object" && typeof data.to_py === "function") {
            try { return data.to_py(); } catch (e) {}
        }
        if (typeof data === "string") {
            try { return JSON.parse(data); } catch (e) { return data; }
        }
        return data;
    }

    window.gb2680Storage = {
        loadHistory: function () {
            return migrateLegacyData().catch(() => {
                try { return JSON.parse(window.localStorage.getItem(LEGACY_HISTORY_KEY) || "[]"); } catch (error) { return []; }
            });
        },
        saveHistory: function (history) {
            const clean = cleanPyProxy(history);
            return write(HISTORY_KEY, clean).catch(() => {
                try { window.localStorage.setItem(LEGACY_HISTORY_KEY, JSON.stringify(clean)); } catch(e) {}
            });
        },
        clearHistory: function () {
            return write(HISTORY_KEY, []).catch(() => {
                window.localStorage.removeItem(LEGACY_HISTORY_KEY);
            });
        },
        loadChart: function () {
            let legacyChart = null;
            try {
                const stored = window.localStorage.getItem(LEGACY_CHART_KEY);
                if (stored) legacyChart = JSON.parse(stored);
            } catch (error) { legacyChart = null; }

            if (legacyChart && legacyChart.spectra && Array.isArray(legacyChart.spectra.wl) && legacyChart.spectra.wl.length > 0) {
                return Promise.resolve(legacyChart);
            }

            return read(CHART_KEY).then(chart => {
                if (chart && chart.spectra && Array.isArray(chart.spectra.wl) && chart.spectra.wl.length > 0) {
                    return chart;
                }
                return legacyChart;
            }).catch(() => legacyChart);
        },
        saveChart: function (chart) {
            const clean = cleanPyProxy(chart);
            try {
                window.localStorage.setItem(LEGACY_CHART_KEY, JSON.stringify(clean));
            } catch (e) {}
            return write(CHART_KEY, clean).catch(() => {});
        }
    };
})();
