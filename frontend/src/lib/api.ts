const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
export function getToken(){return localStorage.getItem('tradepass_token') || '';}
export function setToken(token:string){localStorage.setItem('tradepass_token',token);}
export function clearToken(){localStorage.removeItem('tradepass_token');}
export async function api<T=any>(path:string, options:RequestInit={}):Promise<T>{
 const headers = new Headers(options.headers || {}); const token=getToken(); if(token) headers.set('Authorization',`Bearer ${token}`);
 if(options.body && !(options.body instanceof FormData)) headers.set('Content-Type','application/json');
 const response=await fetch(`${API}${path}`,{...options,headers});
 if(!response.ok){let message=`Request failed (${response.status})`;try{const data=await response.json();message=typeof data.detail==='string'?data.detail:JSON.stringify(data.detail||data);}catch{} throw new Error(message);}
 if(response.status===204) return undefined as T; return response.json();
}
