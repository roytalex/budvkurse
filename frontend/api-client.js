
window.Api = (() => {
  const KEY = 'vkurse-session-v2';
  let tokens = null, refreshJob = null, generation = 0;
  try { tokens = JSON.parse(sessionStorage.getItem(KEY) || 'null'); } catch {}
  const covers = new Map();
  function setTokens(value) {
    tokens = value;
    try { value ? sessionStorage.setItem(KEY, JSON.stringify(value)) : sessionStorage.removeItem(KEY); } catch {}
  }
  function clear() {
    generation++;
    setTokens(null);
    for (const value of covers.values()) value.then(url => URL.revokeObjectURL(url)).catch(() => {});
    covers.clear();
  }
  class ApiError extends Error { constructor(message, status) { super(message); this.status = status; } }
  function errorMessage(data) {
    if (typeof data?.detail === 'string') return data.detail;
    if (Array.isArray(data?.detail)) return data.detail.map(e => `${e.loc?.slice(1).join('.') || 'Данные'}: ${e.msg}`).join('; ');
    return 'Не удалось выполнить запрос. Попробуй ещё раз.';
  }
  async function refresh() {
    if (refreshJob) return refreshJob;
    const epoch = generation;
    const token = tokens?.refresh_token;
    if (!token) throw new ApiError('Войди в аккаунт', 401);
    refreshJob = (async () => {
      const response = await fetch('/api/v1/auth/refresh', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({refresh_token:token})});
      const data = await response.json();
      if (epoch !== generation) throw new ApiError('Сессия завершена', 401);
      if (!response.ok) {
        if (response.status === 401) { clear(); window.dispatchEvent(new Event('session-expired')); }
        throw new ApiError(errorMessage(data), response.status);
      }
      setTokens(data);
    })().finally(() => { refreshJob = null; });
    return refreshJob;
  }
  async function request(path, {method='GET', body, signal, auth=true, blob=false} = {}, retry=true) {
    const epoch = generation;
    const headers = {};
    if (auth && tokens?.access_token) headers.Authorization = `Bearer ${tokens.access_token}`;
    if (body !== undefined && !(body instanceof FormData)) headers['Content-Type'] = 'application/json';
    let response;
    try { response = await fetch('/api/v1'+path, {method, headers, signal, cache:'no-store', body:body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body)}); }
    catch (error) { if (error.name === 'AbortError') throw error; throw new ApiError('Нет связи с сервером. Проверь подключение и повтори.', 0); }
    if (epoch !== generation) throw new ApiError('Сессия завершена', 401);
    if (response.status === 401 && auth && retry && tokens?.refresh_token) {
      await refresh();
      return request(path, {method,body,signal,auth,blob}, false);
    }
    if (response.status === 401 && auth) { clear(); window.dispatchEvent(new Event('session-expired')); }
    if (!response.ok) { const data = await response.json().catch(() => ({})); throw new ApiError(errorMessage(data), response.status); }
    if (response.status === 204) return null;
    const data = await (blob ? response.blob() : response.json());
    if (epoch !== generation) throw new ApiError('Сессия завершена', 401);
    return data;
  }
  const query = values => { const q = new URLSearchParams(); for (const [k,v] of Object.entries(values)) if (v !== '' && v != null) q.set(k,String(v)); return q.toString(); };
  async function all(path, filters={}, signal) {
    const items = [];
    for (let page=1; ; page++) {
      const result = await request(`${path}?${query({...filters,page,limit:100})}`, {signal});
      items.push(...result.items);
      if (!result.items.length || page*result.limit >= result.total) break;
    }
    return items;
  }
  async function login(email,password) {
    const result = await request('/auth/login', {method:'POST',body:{email,password},auth:false});
    generation++; setTokens(result);
  }
  async function logout() {


    if (tokens?.refresh_token) await request('/auth/logout',{method:'POST',body:{refresh_token:tokens.refresh_token},auth:false});
    clear();
  }
  function cover(path) {
    if (!path?.startsWith('/api/v1/files/')) return Promise.reject(new Error('Invalid cover URL'));
    if (!covers.has(path)) covers.set(path, request(path.slice(7), {blob:true}).then(blob => URL.createObjectURL(blob)).catch(e => {covers.delete(path);throw e;}));
    return covers.get(path);
  }
  return {request, all, query, login, logout, clear, cover, hasSession:()=>!!tokens?.refresh_token};
})();
