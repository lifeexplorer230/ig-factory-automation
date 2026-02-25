#!/usr/bin/env node
/**
 * MoreLogin Cloud API — Phone Cloud + Instagram
 * Проект: IG Content Factory
 *
 * API: https://api.morelogin.com (облачный, не локальный)
 * Auth: OAuth2 client_credentials → Bearer JWT (3600s)
 *
 * ВАЖНЫЕ ОТКРЫТИЯ (добыты через отладку):
 *   - client_id в /oauth2/token должен быть INTEGER (не строка!)
 *   - Пути без /api/ префикса: /cloudphone/page (не /api/cloudphone/page)
 *   - proxyInfo/delete принимает RAW JSON array integers: [id1, id2]
 *   - app/install требует appVersionId (не packageName!)
 *   - Прокси ОБЯЗАТЕЛЬНО добавлять через UI или API с proxyProvider:0
 *   - Для SOCKS5 (proxyType:2) credentials сохраняются
 *   - Поиск приложений: /cloudphone/app/page с полем appName в теле
 *
 * Использование:
 *   node morelogin-cloud-api.js
 *   PROXY_ID=1234 node morelogin-cloud-api.js  # если нет телефонов
 */

const https = require('https');

const CONFIG = {
  baseUrl:   'https://api.morelogin.com',
  appId:     Number(process.env.APP_ID) || 1689105551924663,  // INTEGER!
  appSecret: process.env.APP_SECRET || 'b4d061d5c7a24fac84d6f5f3c177e844',
  skuId:     '10004',
  instagramVersionId: '1682134957917431',  // v412.0.0.35.87
  instagramPackage:   'com.instagram.android',
};

// --- HTTP helper ---
function request(method, path, body = null, headers = {}) {
  return new Promise((resolve, reject) => {
    const bodyStr = body !== null ? JSON.stringify(body) : null;
    const req = https.request({
      hostname: 'api.morelogin.com',
      port: 443,
      path,
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(bodyStr ? {'Content-Length': Buffer.byteLength(bodyStr)} : {}),
        ...headers,
      }
    }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try { resolve({status: res.statusCode, data: JSON.parse(data)}); }
        catch(e) { resolve({status: res.statusCode, data}); }
      });
    });
    req.on('error', reject);
    if (bodyStr) req.write(bodyStr);
    req.end();
  });
}

// --- Auth ---
async function getAccessToken() {
  console.log('🔑 Получаем access token...');
  const r = await request('POST', '/oauth2/token', {
    grant_type:    'client_credentials',
    client_id:     CONFIG.appId,   // INTEGER!
    client_secret: CONFIG.appSecret,
  });
  if (r.data?.code === 0 && r.data?.data?.access_token) {
    console.log('   ✅ Token получен, expires_in:', r.data.data.expires_in, 'сек');
    return r.data.data.access_token;
  }
  throw new Error(`Не удалось получить токен: code=${r.data?.code} msg=${r.data?.msg}`);
}

function auth(token) {
  return { 'Authorization': `Bearer ${token}` };
}

// --- Proxy ---
async function addProxy(token, {name, ip, port, username, password}) {
  console.log(`\n🌐 Добавляем прокси ${ip}:${port}...`);
  // proxyProvider:0 ОБЯЗАТЕЛЕН. proxyType:2 = SOCKS5 (credentials сохраняются)
  const r = await request('POST', '/proxyInfo/add', {
    proxyName:         name,
    proxyCategoryType: 2,
    proxyProvider:     0,
    proxyType:         2,
    proxyIp:           ip,
    proxyPort:         port,
    username,
    password,
  }, auth(token));
  if (r.data?.code === 0) {
    console.log('   ✅ Прокси создан, ID:', r.data.data);
    return r.data.data;
  }
  throw new Error(`Ошибка создания прокси: code=${r.data?.code} msg=${r.data?.msg}`);
}

async function deleteProxies(token, ids) {
  // ВАЖНО: тело — raw JSON array integers, не объект!
  const r = await request('POST', '/proxyInfo/delete', ids.map(Number), auth(token));
  return r.data?.code === 0;
}

async function listProxies(token) {
  const r = await request('POST', '/proxyInfo/page', {current: 1, size: 50}, auth(token));
  return r.data?.data?.dataList || [];
}

// --- Cloud Phone ---
async function listPhones(token) {
  const r = await request('POST', '/cloudphone/page', {current: 1, size: 50}, auth(token));
  return r.data?.data?.dataList || [];
}

async function createPhone(token, name, proxyId) {
  console.log(`\n📱 Создаём телефон "${name}" с прокси ${proxyId}...`);
  const r = await request('POST', '/cloudphone/create', {
    envName:  name,
    quantity: 1,
    skuId:    CONFIG.skuId,
    proxyId:  String(proxyId),
  }, auth(token));
  if (r.data?.code === 0) {
    const id = r.data.data[0];
    console.log('   ✅ Телефон создан, ID:', id);
    return id;
  }
  throw new Error(`Ошибка создания телефона: code=${r.data?.code} msg=${r.data?.msg}`);
}

async function powerOn(token, phoneId) {
  console.log(`\n⚡ Запускаем телефон ${phoneId}...`);
  const r = await request('POST', '/cloudphone/powerOn', {id: Number(phoneId)}, auth(token));
  if (r.data?.code === 0) { console.log('   ✅ powerOn принят'); return true; }
  throw new Error(`Ошибка powerOn: code=${r.data?.code} msg=${r.data?.msg}`);
}

async function waitRunning(token, phoneId, timeoutMs = 120000) {
  const start = Date.now();
  const statuses = {0:'New',1:'Failed',2:'Stop',3:'Starting',4:'Running',5:'Resetting'};
  console.log('   ⏳ Ждём Running...');
  while (Date.now() - start < timeoutMs) {
    await new Promise(r => setTimeout(r, 5000));
    const phones = await listPhones(token);
    const p = phones.find(x => String(x.id) === String(phoneId));
    const es = p?.envStatus;
    console.log(`   envStatus=${es}(${statuses[es]||'?'}) proxyStatus=${p?.proxyStatus}`);
    if (es === 4) { console.log('   ✅ Running!'); return true; }
    if (es === 1 || es === 2) throw new Error(`Телефон остановился (envStatus=${es})`);
  }
  throw new Error('Timeout: телефон не запустился за 2 минуты');
}

async function deletePhones(token, ids) {
  const r = await request('POST', '/cloudphone/delete/batch',
    {ids: ids.map(String)}, auth(token));
  return r.data?.code === 0;
}

// --- Apps ---
async function findAppVersion(token, phoneId, appName) {
  // ВАЖНО: поиск через appName в теле запроса, без него только 10 дефолтных приложений
  const r = await request('POST', '/cloudphone/app/page',
    {id: Number(phoneId), appName, current: 1, size: 5}, auth(token));
  const app = r.data?.data?.dataList?.[0];
  if (!app) throw new Error(`Приложение "${appName}" не найдено в каталоге`);
  const latest = app.appVersionList?.[0];
  console.log(`   Найдено: ${app.appName} v${latest?.versionName}, versionId=${latest?.id}`);
  return {appVersionId: latest?.id, packageName: app.packageName};
}

async function installApp(token, phoneId, appVersionId) {
  console.log(`\n📦 Устанавливаем (appVersionId=${appVersionId})...`);
  // ВАЖНО: нужен appVersionId, не packageName!
  const r = await request('POST', '/cloudphone/app/install',
    {id: Number(phoneId), appVersionId: String(appVersionId)}, auth(token));
  if (r.data?.code === 0) { console.log('   ✅ Установка запущена'); return true; }
  throw new Error(`Ошибка установки: code=${r.data?.code} msg=${r.data?.msg}`);
}

async function waitInstalled(token, phoneId, packageName, timeoutMs = 120000) {
  const start = Date.now();
  console.log(`   ⏳ Ждём установки ${packageName}...`);
  while (Date.now() - start < timeoutMs) {
    await new Promise(r => setTimeout(r, 10000));
    const r2 = await request('POST', '/cloudphone/app/installedList',
      {id: Number(phoneId)}, auth(token));
    const apps = r2.data?.data || [];
    if (apps.some(a => a.packageName === packageName)) {
      console.log('   ✅ Установлено!');
      return true;
    }
    console.log(`   Установлено: ${apps.map(a=>a.appName).join(', ') || 'пусто'}`);
  }
  throw new Error(`Timeout: ${packageName} не установился`);
}

async function startApp(token, phoneId, packageName) {
  console.log(`\n🚀 Запускаем ${packageName}...`);
  const r = await request('POST', '/cloudphone/app/start',
    {id: Number(phoneId), packageName}, auth(token));
  if (r.data?.code === 0) { console.log('   ✅ Запущено!'); return true; }
  throw new Error(`Ошибка запуска: code=${r.data?.code} msg=${r.data?.msg}`);
}

// --- Main ---
async function main() {
  console.log('═══════════════════════════════════════════════════');
  console.log('  MoreLogin Cloud API — IG Factory');
  console.log('  Base URL:', CONFIG.baseUrl);
  console.log('  App ID:', CONFIG.appId);
  console.log('═══════════════════════════════════════════════════');

  const token = await getAccessToken();

  // Проверяем существующие телефоны
  const phones = await listPhones(token);
  console.log(`\nТелефонов в аккаунте: ${phones.length}`);

  let phoneId;
  const running = phones.find(p => p.envStatus === 4);
  if (running) {
    phoneId = running.id;
    console.log(`✅ Используем запущенный телефон: ${running.envName} (${phoneId})`);
  } else if (phones.length > 0) {
    phoneId = phones[0].id;
    console.log(`📱 Найден телефон: ${phones[0].envName} (${phoneId}), запускаем...`);
    await powerOn(token, phoneId);
    await waitRunning(token, phoneId);
  } else {
    const proxyId = process.env.PROXY_ID;
    if (!proxyId) {
      throw new Error('Нет телефонов и нет PROXY_ID. Добавьте прокси через UI MoreLogin и укажите PROXY_ID=...');
    }
    phoneId = await createPhone(token, 'IG-1', proxyId);
    await powerOn(token, phoneId);
    await waitRunning(token, phoneId);
  }

  // Ищем Instagram в каталоге
  console.log('\n🔍 Ищем Instagram в каталоге...');
  const {appVersionId, packageName} = await findAppVersion(token, phoneId, 'Instagram');

  // Проверяем, установлен ли уже
  const installedResp = await request('POST', '/cloudphone/app/installedList',
    {id: Number(phoneId)}, auth(token));
  const alreadyInstalled = (installedResp.data?.data || []).some(a => a.packageName === packageName);

  if (!alreadyInstalled) {
    await installApp(token, phoneId, appVersionId);
    await waitInstalled(token, phoneId, packageName);
  } else {
    console.log('\n✅ Instagram уже установлен');
  }

  // Запускаем Instagram
  await startApp(token, phoneId, packageName);

  console.log('\n╔══════════════════════════════════════════════╗');
  console.log('║  ✅ ГОТОВО! Instagram запущен.               ║');
  console.log(`║  Телефон ID: ${phoneId}  ║`);
  console.log('║  Открой телефон в MoreLogin UI и            ║');
  console.log('║  войди в Instagram аккаунт.                 ║');
  console.log('╚══════════════════════════════════════════════╝');
}

main().catch(err => {
  console.error('\n❌ ОШИБКА:', err.message);
  process.exit(1);
});
