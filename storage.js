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

    window.gb2680Storage = {
        loadHistory: function () {
            return migrateLegacyData().catch(() => {
                try { return JSON.parse(window.localStorage.getItem(LEGACY_HISTORY_KEY) || "[]"); } catch (error) { return []; }
            });
        },
        saveHistory: function (history) {
            return write(HISTORY_KEY, history).catch(() => {
                window.localStorage.setItem(LEGACY_HISTORY_KEY, JSON.stringify(history));
            });
        },
        clearHistory: function () {
            return write(HISTORY_KEY, []).catch(() => {
                window.localStorage.removeItem(LEGACY_HISTORY_KEY);
            });
        },
        loadChart: function () {
            return read(CHART_KEY).then(chart => {
                if (chart !== undefined) return chart;
                let legacyChart = null;
                try { legacyChart = JSON.parse(window.localStorage.getItem(LEGACY_CHART_KEY) || "null"); } catch (error) { legacyChart = null; }
                return write(CHART_KEY, legacyChart).then(() => legacyChart);
            }).catch(() => {
                try { return JSON.parse(window.localStorage.getItem(LEGACY_CHART_KEY) || "null"); } catch (error) { return null; }
            });
        },
        saveChart: function (chart) {
            return write(CHART_KEY, chart).catch(() => {
                window.localStorage.setItem(LEGACY_CHART_KEY, JSON.stringify(chart));
            });
        }
    };
})();
