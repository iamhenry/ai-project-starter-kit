#!/usr/bin/env node

/**
 * Astro ASO Query Script
 * Queries the local Astro Mac app SQLite database for ASO data.
 *
 * Usage: node astro-query.mjs <command> '<json-params>'
 */

import { homedir } from "os";
import { existsSync, readFileSync } from "fs";
import { join } from "path";

// Database path for Astro Mac app
const DB_PATH = join(
  homedir(),
  "Library/Containers/matteospada.it.ASO/Data/Library/Application Support/Astro/Model.sqlite",
);

// Output helper
function output(success, data) {
  console.log(
    JSON.stringify(
      success ? { success: true, data } : { success: false, error: data },
    ),
  );
  process.exit(success ? 0 : 1);
}

// Check if Astro app is installed
if (!existsSync(DB_PATH)) {
  output(
    false,
    "Astro app not found. Please install Astro from https://astro.app and add some tracked apps/keywords.",
  );
}

// Dynamic import of sql.js (ESM)
let initSqlJs, db;

async function initDb() {
  try {
    const sqlJs = await import("sql.js");
    initSqlJs = sqlJs.default;

    const SQL = await initSqlJs();
    const dbBuffer = readFileSync(DB_PATH);
    db = new SQL.Database(dbBuffer);

    // Try to load WAL file if exists
    const walPath = DB_PATH + "-wal";
    if (existsSync(walPath)) {
      try {
        // WAL mode requires special handling - we read the main db which should have checkpointed data
        // For most use cases, the main db file contains recent enough data
      } catch (e) {
        // Ignore WAL errors, continue with main db
      }
    }
  } catch (e) {
    output(
      false,
      `Failed to open database: ${e.message}. Make sure sql.js is installed: npm install sql.js`,
    );
  }
}

// Query helper
function query(sql, params = []) {
  try {
    const stmt = db.prepare(sql);
    stmt.bind(params);
    const results = [];
    while (stmt.step()) {
      results.push(stmt.getAsObject());
    }
    stmt.free();
    return results;
  } catch (e) {
    throw new Error(`Query failed: ${e.message}`);
  }
}

function queryOne(sql, params = []) {
  const results = query(sql, params);
  return results.length > 0 ? results[0] : null;
}

// ============================================
// COMMAND IMPLEMENTATIONS
// ============================================

function listApps() {
  const apps = query(`
    SELECT 
      ZAPP.Z_PK as id,
      ZAPP.ZNAME as name,
      ZAPP.ZAPPID as appId,
      ZAPP.ZDEVELOPER as developer,
      ZAPP.ZPLATFORM as platform
    FROM ZAPP
    ORDER BY ZAPP.ZNAME
  `);

  return apps.map((app) => ({
    id: app.id,
    name: app.name,
    appId: app.appId,
    developer: app.developer,
    platform: app.platform === 0 ? "ios" : "mac",
  }));
}

function searchRankings(params) {
  const { keyword, store, appName, appId } = params;

  if (!keyword) {
    throw new Error("keyword parameter is required");
  }

  let sql = `
    SELECT 
      ZAPP.ZNAME as appName,
      ZKEYWORD.ZTEXT as keyword,
      ZKEYWORD.ZCURRENTRANKING as currentRanking,
      ZKEYWORD.ZPREVIOUSRANKING as previousRanking,
      ZKEYWORD.ZDIFFICULTY as difficulty,
      ZKEYWORD.ZPOPULARITY as popularity,
      ZKEYWORD.ZSTORE as store,
      ZKEYWORD.ZLASTUPDATE as lastUpdate
    FROM ZKEYWORD
    JOIN ZAPP ON ZKEYWORD.ZAPP = ZAPP.Z_PK
    WHERE LOWER(ZKEYWORD.ZTEXT) LIKE LOWER(?)
  `;

  const queryParams = [`%${keyword}%`];

  if (store) {
    sql += ` AND LOWER(ZKEYWORD.ZSTORE) = LOWER(?)`;
    queryParams.push(store);
  }

  if (appName) {
    sql += ` AND LOWER(ZAPP.ZNAME) LIKE LOWER(?)`;
    queryParams.push(`%${appName}%`);
  }

  if (appId) {
    sql += ` AND ZAPP.ZAPPID = ?`;
    queryParams.push(appId);
  }

  sql += ` ORDER BY ZKEYWORD.ZCURRENTRANKING ASC NULLS LAST`;

  const results = query(sql, queryParams);

  return results.map((r) => ({
    app: r.appName,
    keyword: r.keyword,
    currentRanking: r.currentRanking,
    previousRanking: r.previousRanking,
    difficulty: r.difficulty,
    popularity: r.popularity,
    store: r.store,
    lastUpdate: r.lastUpdate
      ? new Date(r.lastUpdate * 1000 + Date.UTC(2001, 0, 1)).toISOString()
      : null,
  }));
}

function historicalRankings(params) {
  const { keyword, appName, appId, daysBack = 30, store } = params;

  if (!keyword) {
    throw new Error("keyword parameter is required");
  }

  const cutoffDate =
    (Date.now() - daysBack * 24 * 60 * 60 * 1000 - Date.UTC(2001, 0, 1)) / 1000;

  let sql = `
    SELECT 
      ZKEYWORD.ZTEXT as keyword,
      ZAPP.ZNAME as appName,
      ZKEYWORD.ZSTORE as store,
      ZRANKINGDATAPOINT.ZRANKING as ranking,
      ZRANKINGDATAPOINT.ZDATE as date
    FROM ZRANKINGDATAPOINT
    JOIN ZKEYWORD ON ZRANKINGDATAPOINT.ZKEYWORD = ZKEYWORD.Z_PK
    JOIN ZAPP ON ZKEYWORD.ZAPP = ZAPP.Z_PK
    WHERE LOWER(ZKEYWORD.ZTEXT) LIKE LOWER(?)
    AND ZRANKINGDATAPOINT.ZDATE >= ?
  `;

  const queryParams = [`%${keyword}%`, cutoffDate];

  if (store) {
    sql += ` AND LOWER(ZKEYWORD.ZSTORE) = LOWER(?)`;
    queryParams.push(store);
  }

  if (appName) {
    sql += ` AND LOWER(ZAPP.ZNAME) LIKE LOWER(?)`;
    queryParams.push(`%${appName}%`);
  }

  if (appId) {
    sql += ` AND ZAPP.ZAPPID = ?`;
    queryParams.push(appId);
  }

  sql += ` ORDER BY ZRANKINGDATAPOINT.ZDATE ASC`;

  const results = query(sql, queryParams);

  // Group by keyword+app
  const grouped = {};
  for (const r of results) {
    const key = `${r.appName}|${r.keyword}|${r.store}`;
    if (!grouped[key]) {
      grouped[key] = {
        keyword: r.keyword,
        app: r.appName,
        store: r.store,
        rankings: [],
      };
    }
    grouped[key].rankings.push({
      date: new Date(r.date * 1000 + Date.UTC(2001, 0, 1))
        .toISOString()
        .split("T")[0],
      ranking: r.ranking,
    });
  }

  return Object.values(grouped);
}

function appKeywords(params) {
  const { appName, appId, store } = params;

  if (!appName && !appId) {
    throw new Error("Either appName or appId parameter is required");
  }

  let sql = `
    SELECT 
      ZAPP.ZNAME as appName,
      ZKEYWORD.ZTEXT as keyword,
      ZKEYWORD.ZCURRENTRANKING as currentRanking,
      ZKEYWORD.ZPREVIOUSRANKING as previousRanking,
      ZKEYWORD.ZDIFFICULTY as difficulty,
      ZKEYWORD.ZPOPULARITY as popularity,
      ZKEYWORD.ZSTORE as store,
      ZKEYWORD.ZAPPSCOUNT as appsCount,
      ZKEYWORD.ZLASTUPDATE as lastUpdate
    FROM ZKEYWORD
    JOIN ZAPP ON ZKEYWORD.ZAPP = ZAPP.Z_PK
    WHERE 1=1
  `;

  const queryParams = [];

  if (appName) {
    sql += ` AND LOWER(ZAPP.ZNAME) LIKE LOWER(?)`;
    queryParams.push(`%${appName}%`);
  }

  if (appId) {
    sql += ` AND ZAPP.ZAPPID = ?`;
    queryParams.push(appId);
  }

  if (store) {
    sql += ` AND LOWER(ZKEYWORD.ZSTORE) = LOWER(?)`;
    queryParams.push(store);
  }

  sql += ` ORDER BY ZKEYWORD.ZCURRENTRANKING ASC NULLS LAST`;

  const results = query(sql, queryParams);

  return results.map((r) => ({
    app: r.appName,
    keyword: r.keyword,
    currentRanking: r.currentRanking,
    previousRanking: r.previousRanking,
    difficulty: r.difficulty,
    popularity: r.popularity,
    appsCount: r.appsCount,
    store: r.store,
    lastUpdate: r.lastUpdate
      ? new Date(r.lastUpdate * 1000 + Date.UTC(2001, 0, 1)).toISOString()
      : null,
  }));
}

function keywordTrends(params) {
  const { keyword, appName, appId, period = "month", store } = params;

  if (!keyword) {
    throw new Error("keyword parameter is required");
  }

  const periodDays = {
    week: 7,
    month: 30,
    year: 365,
    all: 3650,
  };

  const daysBack = periodDays[period] || 30;
  const cutoffDate =
    (Date.now() - daysBack * 24 * 60 * 60 * 1000 - Date.UTC(2001, 0, 1)) / 1000;

  let sql = `
    SELECT 
      ZKEYWORD.ZTEXT as keyword,
      ZAPP.ZNAME as appName,
      ZKEYWORD.ZSTORE as store,
      ZRANKINGDATAPOINT.ZRANKING as ranking,
      ZRANKINGDATAPOINT.ZDATE as date
    FROM ZRANKINGDATAPOINT
    JOIN ZKEYWORD ON ZRANKINGDATAPOINT.ZKEYWORD = ZKEYWORD.Z_PK
    JOIN ZAPP ON ZKEYWORD.ZAPP = ZAPP.Z_PK
    WHERE LOWER(ZKEYWORD.ZTEXT) LIKE LOWER(?)
    AND ZRANKINGDATAPOINT.ZDATE >= ?
  `;

  const queryParams = [`%${keyword}%`, cutoffDate];

  if (store) {
    sql += ` AND LOWER(ZKEYWORD.ZSTORE) = LOWER(?)`;
    queryParams.push(store);
  }

  if (appName) {
    sql += ` AND LOWER(ZAPP.ZNAME) LIKE LOWER(?)`;
    queryParams.push(`%${appName}%`);
  }

  if (appId) {
    sql += ` AND ZAPP.ZAPPID = ?`;
    queryParams.push(appId);
  }

  sql += ` ORDER BY ZRANKINGDATAPOINT.ZDATE ASC`;

  const results = query(sql, queryParams);

  if (results.length === 0) {
    return { message: "No ranking data found for this keyword" };
  }

  // Group and analyze
  const grouped = {};
  for (const r of results) {
    const key = `${r.appName}|${r.keyword}|${r.store}`;
    if (!grouped[key]) {
      grouped[key] = {
        keyword: r.keyword,
        app: r.appName,
        store: r.store,
        rankings: [],
      };
    }
    grouped[key].rankings.push(r.ranking);
  }

  return Object.values(grouped).map((g) => {
    const rankings = g.rankings;
    const avg = rankings.reduce((a, b) => a + b, 0) / rankings.length;
    const min = Math.min(...rankings);
    const max = Math.max(...rankings);
    const variance =
      rankings.reduce((sum, r) => sum + Math.pow(r - avg, 2), 0) /
      rankings.length;
    const stdDev = Math.sqrt(variance);

    // Determine trend
    const firstHalf = rankings.slice(0, Math.floor(rankings.length / 2));
    const secondHalf = rankings.slice(Math.floor(rankings.length / 2));
    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;

    let trend = "stable";
    if (secondAvg < firstAvg - 2) trend = "improving";
    else if (secondAvg > firstAvg + 2) trend = "declining";

    return {
      keyword: g.keyword,
      app: g.app,
      store: g.store,
      period,
      dataPoints: rankings.length,
      avgRanking: Math.round(avg * 10) / 10,
      minRanking: min,
      maxRanking: max,
      volatility: Math.round(stdDev * 10) / 10,
      trend,
    };
  });
}

function compareRankings(params) {
  const { keyword, date1, date2, appName, appId, store } = params;

  if (!keyword || !date1 || !date2) {
    throw new Error("keyword, date1, and date2 parameters are required");
  }

  // Convert ISO dates to Core Data timestamps
  const ts1 = (new Date(date1).getTime() - Date.UTC(2001, 0, 1)) / 1000;
  const ts2 = (new Date(date2).getTime() - Date.UTC(2001, 0, 1)) / 1000;

  // Get rankings near each date
  const getRankingsNearDate = (targetTs) => {
    let sql = `
      SELECT 
        ZKEYWORD.ZTEXT as keyword,
        ZAPP.ZNAME as appName,
        ZKEYWORD.ZSTORE as store,
        ZRANKINGDATAPOINT.ZRANKING as ranking,
        ZRANKINGDATAPOINT.ZDATE as date
      FROM ZRANKINGDATAPOINT
      JOIN ZKEYWORD ON ZRANKINGDATAPOINT.ZKEYWORD = ZKEYWORD.Z_PK
      JOIN ZAPP ON ZKEYWORD.ZAPP = ZAPP.Z_PK
      WHERE LOWER(ZKEYWORD.ZTEXT) LIKE LOWER(?)
      AND ABS(ZRANKINGDATAPOINT.ZDATE - ?) < 86400
    `;

    const queryParams = [`%${keyword}%`, targetTs];

    if (store) {
      sql += ` AND LOWER(ZKEYWORD.ZSTORE) = LOWER(?)`;
      queryParams.push(store);
    }

    if (appName) {
      sql += ` AND LOWER(ZAPP.ZNAME) LIKE LOWER(?)`;
      queryParams.push(`%${appName}%`);
    }

    if (appId) {
      sql += ` AND ZAPP.ZAPPID = ?`;
      queryParams.push(appId);
    }

    return query(sql, queryParams);
  };

  const rankings1 = getRankingsNearDate(ts1);
  const rankings2 = getRankingsNearDate(ts2);

  // Build comparison
  const comparisons = [];
  const r1Map = new Map(
    rankings1.map((r) => [`${r.appName}|${r.keyword}|${r.store}`, r]),
  );

  for (const r2 of rankings2) {
    const key = `${r2.appName}|${r2.keyword}|${r2.store}`;
    const r1 = r1Map.get(key);

    comparisons.push({
      keyword: r2.keyword,
      app: r2.appName,
      store: r2.store,
      rankingDate1: r1 ? r1.ranking : null,
      rankingDate2: r2.ranking,
      change: r1 ? r1.ranking - r2.ranking : null,
      date1,
      date2,
    });
  }

  return comparisons;
}

function appRatings(params) {
  const { appName, appId, store, daysBack = 30 } = params;

  if (!appName && !appId) {
    throw new Error("Either appName or appId parameter is required");
  }

  const cutoffDate =
    (Date.now() - daysBack * 24 * 60 * 60 * 1000 - Date.UTC(2001, 0, 1)) / 1000;

  let sql = `
    SELECT 
      ZAPP.ZNAME as appName,
      ZRATING.ZAVERAGEUSERRATING as avgRating,
      ZRATING.ZUSERRATINGCOUNT as ratingCount,
      ZRATING.ZCOUNTRYNAME as country,
      ZRATING.ZSTORE as store,
      ZRATING.ZDATE as date
    FROM ZRATING
    JOIN ZAPP ON ZRATING.ZAPP = ZAPP.Z_PK
    WHERE ZRATING.ZDATE >= ?
  `;

  const queryParams = [cutoffDate];

  if (appName) {
    sql += ` AND LOWER(ZAPP.ZNAME) LIKE LOWER(?)`;
    queryParams.push(`%${appName}%`);
  }

  if (appId) {
    sql += ` AND ZAPP.ZAPPID = ?`;
    queryParams.push(appId);
  }

  if (store) {
    sql += ` AND LOWER(ZRATING.ZSTORE) = LOWER(?)`;
    queryParams.push(store);
  }

  sql += ` ORDER BY ZRATING.ZDATE DESC`;

  const results = query(sql, queryParams);

  return results.map((r) => ({
    app: r.appName,
    avgRating: r.avgRating,
    ratingCount: r.ratingCount,
    country: r.country,
    store: r.store,
    date: new Date(r.date * 1000 + Date.UTC(2001, 0, 1))
      .toISOString()
      .split("T")[0],
  }));
}

function keywordCompetitors(params) {
  const { keyword, store, limit = 10 } = params;

  if (!keyword) {
    throw new Error("keyword parameter is required");
  }

  // This queries the apps that rank for the same keyword
  let sql = `
    SELECT 
      ZKEYWORD.ZTEXT as keyword,
      ZAPP.ZNAME as appName,
      ZAPP.ZAPPID as appId,
      ZKEYWORD.ZCURRENTRANKING as ranking,
      ZKEYWORD.ZSTORE as store
    FROM ZKEYWORD
    JOIN ZAPP ON ZKEYWORD.ZAPP = ZAPP.Z_PK
    WHERE LOWER(ZKEYWORD.ZTEXT) LIKE LOWER(?)
    AND ZKEYWORD.ZCURRENTRANKING IS NOT NULL
  `;

  const queryParams = [`%${keyword}%`];

  if (store) {
    sql += ` AND LOWER(ZKEYWORD.ZSTORE) = LOWER(?)`;
    queryParams.push(store);
  }

  sql += ` ORDER BY ZKEYWORD.ZCURRENTRANKING ASC LIMIT ?`;
  queryParams.push(limit);

  const results = query(sql, queryParams);

  return {
    keyword,
    store: store || "all",
    competitors: results.map((r) => ({
      appName: r.appName,
      appId: r.appId,
      ranking: r.ranking,
    })),
  };
}

function keywordRecommendations(params) {
  const { keyword, appName, appId, store, limit = 10 } = params;

  if (!keyword) {
    throw new Error("keyword parameter is required");
  }

  // Find similar keywords based on shared words
  const words = keyword.toLowerCase().split(/\s+/);
  const likePatterns = words.map((w) => `%${w}%`);

  let sql = `
    SELECT DISTINCT
      ZKEYWORD.ZTEXT as keyword,
      ZKEYWORD.ZDIFFICULTY as difficulty,
      ZKEYWORD.ZPOPULARITY as popularity,
      ZKEYWORD.ZSTORE as store
    FROM ZKEYWORD
    WHERE ZKEYWORD.ZTEXT != ?
    AND (${words.map(() => "LOWER(ZKEYWORD.ZTEXT) LIKE ?").join(" OR ")})
  `;

  const queryParams = [keyword, ...likePatterns];

  if (store) {
    sql += ` AND LOWER(ZKEYWORD.ZSTORE) = LOWER(?)`;
    queryParams.push(store);
  }

  sql += ` ORDER BY ZKEYWORD.ZPOPULARITY DESC NULLS LAST LIMIT ?`;
  queryParams.push(limit);

  const results = query(sql, queryParams);

  return {
    keyword,
    store: store || "all",
    recommendedKeywords: results.map((r) => ({
      keyword: r.keyword,
      difficulty: r.difficulty,
      popularity: r.popularity,
      store: r.store,
    })),
  };
}

function competitiveLandscape(params) {
  const { appName, appId, store, limit = 10 } = params;

  if (!appName && !appId) {
    throw new Error("Either appName or appId parameter is required");
  }

  // Get all keywords for the app
  const appKeywordsList = appKeywords({ appName, appId, store });

  if (appKeywordsList.length === 0) {
    return { message: "No keywords found for this app" };
  }

  // Analyze ranking distribution
  const rankings = appKeywordsList
    .filter((k) => k.currentRanking !== null)
    .map((k) => k.currentRanking);
  const top10 = rankings.filter((r) => r <= 10).length;
  const top25 = rankings.filter((r) => r <= 25).length;
  const top50 = rankings.filter((r) => r <= 50).length;

  const marketShare = {
    top10: Math.round((top10 / rankings.length) * 100),
    top25: Math.round((top25 / rankings.length) * 100),
    top50: Math.round((top50 / rankings.length) * 100),
  };

  let competitiveIntensity = "low";
  if (marketShare.top10 < 20) competitiveIntensity = "high";
  else if (marketShare.top10 < 40) competitiveIntensity = "medium";

  return {
    app: appName || appId,
    store: store || "all",
    totalKeywords: appKeywordsList.length,
    rankedKeywords: rankings.length,
    marketShare,
    competitiveIntensity,
    avgRanking:
      rankings.length > 0
        ? Math.round(rankings.reduce((a, b) => a + b, 0) / rankings.length)
        : null,
  };
}

function keywordOpportunities(params) {
  const {
    appName,
    appId,
    store,
    minPopularity = 20,
    maxDifficulty = 50,
  } = params;

  if (!appName && !appId) {
    throw new Error("Either appName or appId parameter is required");
  }

  let sql = `
    SELECT 
      ZKEYWORD.ZTEXT as keyword,
      ZKEYWORD.ZCURRENTRANKING as currentRanking,
      ZKEYWORD.ZDIFFICULTY as difficulty,
      ZKEYWORD.ZPOPULARITY as popularity,
      ZKEYWORD.ZAPPSCOUNT as competition,
      ZKEYWORD.ZSTORE as store
    FROM ZKEYWORD
    JOIN ZAPP ON ZKEYWORD.ZAPP = ZAPP.Z_PK
    WHERE ZKEYWORD.ZPOPULARITY >= ?
    AND ZKEYWORD.ZDIFFICULTY <= ?
  `;

  const queryParams = [minPopularity, maxDifficulty];

  if (appName) {
    sql += ` AND LOWER(ZAPP.ZNAME) LIKE LOWER(?)`;
    queryParams.push(`%${appName}%`);
  }

  if (appId) {
    sql += ` AND ZAPP.ZAPPID = ?`;
    queryParams.push(appId);
  }

  if (store) {
    sql += ` AND LOWER(ZKEYWORD.ZSTORE) = LOWER(?)`;
    queryParams.push(store);
  }

  sql += ` ORDER BY (ZKEYWORD.ZPOPULARITY - ZKEYWORD.ZDIFFICULTY) DESC`;

  const results = query(sql, queryParams);

  return results.map((r) => {
    const opportunityScore = Math.round(
      ((r.popularity || 0) - (r.difficulty || 0) + 100) / 2,
    );
    let reasoning = "";

    if (r.currentRanking === null) {
      reasoning = "Not currently ranking - potential new opportunity";
    } else if (r.currentRanking > 50) {
      reasoning = `Currently ranking ${r.currentRanking} - room for improvement`;
    } else if (r.currentRanking > 10) {
      reasoning = `Ranking ${r.currentRanking} - push to top 10`;
    } else {
      reasoning = `Top 10 at position ${r.currentRanking} - maintain position`;
    }

    return {
      keyword: r.keyword,
      store: r.store,
      opportunityScore,
      currentRanking: r.currentRanking,
      difficulty: r.difficulty,
      popularity: r.popularity,
      competition: r.competition,
      reasoning,
    };
  });
}

function rankingAnomalies(params) {
  const { appName, appId, daysBack = 7, threshold = 10, store } = params;

  if (!appName && !appId) {
    throw new Error("Either appName or appId parameter is required");
  }

  // Get keywords with significant ranking changes
  let sql = `
    SELECT 
      ZKEYWORD.ZTEXT as keyword,
      ZAPP.ZNAME as appName,
      ZKEYWORD.ZCURRENTRANKING as currentRanking,
      ZKEYWORD.ZPREVIOUSRANKING as previousRanking,
      ZKEYWORD.ZSTORE as store,
      ZKEYWORD.ZLASTUPDATE as lastUpdate
    FROM ZKEYWORD
    JOIN ZAPP ON ZKEYWORD.ZAPP = ZAPP.Z_PK
    WHERE ZKEYWORD.ZCURRENTRANKING IS NOT NULL
    AND ZKEYWORD.ZPREVIOUSRANKING IS NOT NULL
    AND ABS(ZKEYWORD.ZCURRENTRANKING - ZKEYWORD.ZPREVIOUSRANKING) >= ?
  `;

  const queryParams = [threshold];

  if (appName) {
    sql += ` AND LOWER(ZAPP.ZNAME) LIKE LOWER(?)`;
    queryParams.push(`%${appName}%`);
  }

  if (appId) {
    sql += ` AND ZAPP.ZAPPID = ?`;
    queryParams.push(appId);
  }

  if (store) {
    sql += ` AND LOWER(ZKEYWORD.ZSTORE) = LOWER(?)`;
    queryParams.push(store);
  }

  sql += ` ORDER BY ABS(ZKEYWORD.ZCURRENTRANKING - ZKEYWORD.ZPREVIOUSRANKING) DESC`;

  const results = query(sql, queryParams);

  return results.map((r) => {
    const change = r.previousRanking - r.currentRanking;
    const percentChange = Math.round((change / r.previousRanking) * 100);

    let anomalyType, severity, interpretation;

    if (change > 0) {
      anomalyType = "sudden_rise";
      interpretation = `Ranking improved by ${change} positions`;
    } else {
      anomalyType = "sudden_drop";
      interpretation = `Ranking dropped by ${Math.abs(change)} positions`;
    }

    const absChange = Math.abs(change);
    if (absChange >= 50) severity = "critical";
    else if (absChange >= 25) severity = "high";
    else if (absChange >= 15) severity = "medium";
    else severity = "low";

    return {
      keyword: r.keyword,
      app: r.appName,
      store: r.store,
      previousRanking: r.previousRanking,
      currentRanking: r.currentRanking,
      change,
      percentChange,
      anomalyType,
      severity,
      interpretation,
      detectedDate: r.lastUpdate
        ? new Date(r.lastUpdate * 1000 + Date.UTC(2001, 0, 1)).toISOString()
        : null,
    };
  });
}

function rankingPredictions(params) {
  const { keyword, appName, appId, store, daysForward = 7 } = params;

  if (!keyword) {
    throw new Error("keyword parameter is required");
  }

  // Get historical data for trend analysis
  const history = historicalRankings({
    keyword,
    appName,
    appId,
    store,
    daysBack: 30,
  });

  if (!history || history.length === 0) {
    return { message: "Insufficient historical data for prediction" };
  }

  return history.map((h) => {
    if (h.rankings.length < 3) {
      return {
        keyword: h.keyword,
        app: h.app,
        store: h.store,
        message: "Insufficient data points for prediction",
      };
    }

    const rankings = h.rankings.map((r) => r.ranking);
    const currentRanking = rankings[rankings.length - 1];

    // Simple linear regression
    const n = rankings.length;
    const xSum = (n * (n - 1)) / 2;
    const ySum = rankings.reduce((a, b) => a + b, 0);
    const xySum = rankings.reduce((sum, y, x) => sum + x * y, 0);
    const xxSum = (n * (n - 1) * (2 * n - 1)) / 6;

    const slope = (n * xySum - xSum * ySum) / (n * xxSum - xSum * xSum);
    const intercept = (ySum - slope * xSum) / n;

    const predictedRanking = Math.round(intercept + slope * (n + daysForward));
    const boundedPrediction = Math.max(1, Math.min(200, predictedRanking));

    let trend = "stable";
    if (slope < -0.5) trend = "improving";
    else if (slope > 0.5) trend = "declining";

    // Confidence based on data consistency
    const variance =
      rankings.reduce((sum, r) => sum + Math.pow(r - ySum / n, 2), 0) / n;
    const stdDev = Math.sqrt(variance);
    const confidence = Math.max(0.3, Math.min(0.9, 1 - stdDev / 50));

    return {
      keyword: h.keyword,
      app: h.app,
      store: h.store,
      currentRanking,
      predictedRanking: boundedPrediction,
      confidence: Math.round(confidence * 100),
      trend,
      predictedChange: currentRanking - boundedPrediction,
      predictionDate: new Date(Date.now() + daysForward * 24 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0],
      methodology: "Linear regression on 30-day historical data",
      dataPoints: rankings.length,
    };
  });
}

function lowCompetitionKeywords(params) {
  const { store, maxDifficulty = 30, minPopularity = 20, limit = 20 } = params;

  let sql = `
    SELECT DISTINCT
      ZKEYWORD.ZTEXT as keyword,
      ZKEYWORD.ZDIFFICULTY as difficulty,
      ZKEYWORD.ZPOPULARITY as popularity,
      ZKEYWORD.ZAPPSCOUNT as appsCount,
      ZKEYWORD.ZSTORE as store
    FROM ZKEYWORD
    WHERE ZKEYWORD.ZDIFFICULTY <= ?
    AND ZKEYWORD.ZPOPULARITY >= ?
    AND ZKEYWORD.ZDIFFICULTY IS NOT NULL
    AND ZKEYWORD.ZPOPULARITY IS NOT NULL
  `;

  const queryParams = [maxDifficulty, minPopularity];

  if (store) {
    sql += ` AND LOWER(ZKEYWORD.ZSTORE) = LOWER(?)`;
    queryParams.push(store);
  }

  sql += ` ORDER BY (ZKEYWORD.ZPOPULARITY - ZKEYWORD.ZDIFFICULTY) DESC LIMIT ?`;
  queryParams.push(limit);

  const results = query(sql, queryParams);

  return results.map((r) => ({
    keyword: r.keyword,
    difficulty: r.difficulty,
    popularity: r.popularity,
    competitionScore: Math.round(100 - r.difficulty + r.popularity / 2),
    appsCount: r.appsCount,
    store: r.store,
  }));
}

function analyzeAsoHealth(params) {
  const { appName, appId, store } = params;

  if (!appName && !appId) {
    throw new Error("Either appName or appId parameter is required");
  }

  // Get all data
  const keywords = appKeywords({ appName, appId, store });
  const landscape = competitiveLandscape({ appName, appId, store });

  if (keywords.length === 0) {
    return { message: "No keywords found for this app" };
  }

  // Calculate metrics
  const rankedKeywords = keywords.filter((k) => k.currentRanking !== null);
  const rankings = rankedKeywords.map((k) => k.currentRanking);

  const avgRanking =
    rankings.length > 0
      ? Math.round(rankings.reduce((a, b) => a + b, 0) / rankings.length)
      : null;

  const avgDifficulty =
    keywords.filter((k) => k.difficulty !== null).length > 0
      ? Math.round(
          keywords
            .filter((k) => k.difficulty !== null)
            .reduce((a, k) => a + k.difficulty, 0) /
            keywords.filter((k) => k.difficulty !== null).length,
        )
      : null;

  const avgPopularity =
    keywords.filter((k) => k.popularity !== null).length > 0
      ? Math.round(
          keywords
            .filter((k) => k.popularity !== null)
            .reduce((a, k) => a + k.popularity, 0) /
            keywords.filter((k) => k.popularity !== null).length,
        )
      : null;

  // Improvement trends
  const improving = rankedKeywords.filter(
    (k) => k.previousRanking !== null && k.currentRanking < k.previousRanking,
  ).length;
  const declining = rankedKeywords.filter(
    (k) => k.previousRanking !== null && k.currentRanking > k.previousRanking,
  ).length;
  const stable = rankedKeywords.length - improving - declining;

  // Health score (0-100)
  let healthScore = 50;
  if (landscape.marketShare) {
    healthScore += landscape.marketShare.top10 * 0.3;
    healthScore += landscape.marketShare.top25 * 0.1;
  }
  if (improving > declining) healthScore += 10;
  if (declining > improving) healthScore -= 10;
  if (avgDifficulty && avgDifficulty < 40) healthScore += 5;
  if (avgPopularity && avgPopularity > 40) healthScore += 5;

  healthScore = Math.max(0, Math.min(100, Math.round(healthScore)));

  let healthStatus = "good";
  if (healthScore < 40) healthStatus = "needs_attention";
  else if (healthScore < 60) healthStatus = "fair";
  else if (healthScore >= 80) healthStatus = "excellent";

  return {
    app: appName || appId,
    store: store || "all",
    healthScore,
    healthStatus,
    metrics: {
      totalKeywords: keywords.length,
      rankedKeywords: rankedKeywords.length,
      avgRanking,
      avgDifficulty,
      avgPopularity,
    },
    trends: {
      improving,
      declining,
      stable,
    },
    marketShare: landscape.marketShare || null,
    competitiveIntensity: landscape.competitiveIntensity || null,
    recommendations: generateRecommendations(
      healthScore,
      landscape,
      { improving, declining },
      avgRanking,
    ),
  };
}

function generateRecommendations(healthScore, landscape, trends, avgRanking) {
  const recs = [];

  if (healthScore < 60) {
    recs.push(
      "Focus on improving rankings for existing keywords before adding new ones",
    );
  }

  if (landscape.marketShare && landscape.marketShare.top10 < 20) {
    recs.push(
      "Target more achievable keywords - current portfolio is too competitive",
    );
  }

  if (trends.declining > trends.improving) {
    recs.push(
      "Investigate recent ranking drops - may indicate algorithm changes or competitor activity",
    );
  }

  if (avgRanking && avgRanking > 50) {
    recs.push(
      "Average ranking is low - consider refreshing app metadata and screenshots",
    );
  }

  if (recs.length === 0) {
    recs.push("ASO health is good - continue monitoring and optimizing");
  }

  return recs;
}

// ============================================
// COMMAND ROUTER
// ============================================

const commands = {
  list_apps: listApps,
  search_rankings: searchRankings,
  historical_rankings: historicalRankings,
  app_keywords: appKeywords,
  keyword_trends: keywordTrends,
  compare_rankings: compareRankings,
  app_ratings: appRatings,
  keyword_competitors: keywordCompetitors,
  keyword_recommendations: keywordRecommendations,
  competitive_landscape: competitiveLandscape,
  keyword_opportunities: keywordOpportunities,
  ranking_anomalies: rankingAnomalies,
  ranking_predictions: rankingPredictions,
  low_competition_keywords: lowCompetitionKeywords,
  analyze_aso_health: analyzeAsoHealth,
};

async function main() {
  const [, , command, paramsJson] = process.argv;

  if (!command) {
    output(
      false,
      `Usage: node astro-query.mjs <command> '<json-params>'\n\nAvailable commands: ${Object.keys(commands).join(", ")}`,
    );
  }

  if (!commands[command]) {
    output(
      false,
      `Unknown command: ${command}\n\nAvailable commands: ${Object.keys(commands).join(", ")}`,
    );
  }

  let params = {};
  if (paramsJson) {
    try {
      params = JSON.parse(paramsJson);
    } catch (e) {
      output(false, `Invalid JSON params: ${e.message}`);
    }
  }

  await initDb();

  try {
    const result = commands[command](params);
    output(true, result);
  } catch (e) {
    output(false, e.message);
  }
}

main();
