/* Validates the public snapshot format in both the studio and the storage worker. */
(() => {
  'use strict';

  const VERSION_IDS = ['v1', 'v2', 'v3'];
  const TYPES = ['confirmed', 'uncertain', 'filler'];
  const WEB_IMAGE = /^data:image\/(?:png|jpe?g);base64,[A-Za-z0-9+/=]+$/i;

  function cleanMeta(meta, order) {
    if (!meta || typeof meta !== 'object' || !/^FR-[A-Za-z0-9_-]+$/.test(meta.id) ||
        typeof meta.title !== 'string' || !meta.title.trim() || typeof meta.author !== 'string' ||
        !order.includes(meta.finalId) || !meta.versions) throw Error('Invalid package details');
    const versions = {};
    for (const id of order) {
      const record = meta.versions[id];
      if (!record || !['sketch','iteration','final'].includes(record.kind)) throw Error('Invalid version details');
      const version = {id, kind:record.kind};
      for (const key of ['title','name','tool','model','aiUse','prompt','why','summary','alt','filename']) {
        if (record[key] != null && typeof record[key] !== 'string') throw Error('Invalid version text');
        version[key] = record[key] || '';
      }
      if (!version.title) version.title = version.name || id;
      versions[id] = version;
    }
    return {id:meta.id, title:meta.title, author:meta.author, finalId:meta.finalId, versions};
  }

  function safeState(raw) {
    if (!raw || !Array.isArray(raw.notes) || !Array.isArray(raw.order)) throw Error('Invalid package');
    const order = [...raw.order];
    const validId = id => typeof id === 'string' && /^[a-zA-Z0-9][a-zA-Z0-9_-]*$/.test(id) &&
      !Object.prototype.hasOwnProperty.call(Object.prototype,id) && id !== 'prototype';
    if (!order.length || new Set(order).size !== order.length || !order.every(validId)) throw Error('Invalid version history');
    const meta = raw.meta == null ? null : cleanMeta(raw.meta,order);
    if (!meta && (order.length !== VERSION_IDS.length || !order.every(id=>VERSION_IDS.includes(id)))) {
      throw Error('Invalid demo history');
    }
    const usedIds = new Set();
    const notes = raw.notes.map(note => {
      if (!note || !order.includes(note.version) || !TYPES.includes(note.type) ||
          typeof note.title !== 'string' || typeof note.body !== 'string' ||
          ![note.x, note.y, note.r].every(v => Number.isFinite(v) && v >= 0 && v <= 1) ||
          note.r === 0 || !Number.isSafeInteger(note.id) || note.id < 1 || usedIds.has(note.id)) {
        throw Error('Invalid circle note');
      }
      usedIds.add(note.id);
      const {id,version,type,x,y,r,title,body} = note;
      return {id,version,type,x,y,r,title,body,short:typeof note.short === 'string' ? note.short : title};
    });
    const images = {};
    for (const id of order) {
      const image = raw.images?.[id];
      if (!image && !meta) continue;
      if (typeof image !== 'string' || !WEB_IMAGE.test(image)) throw Error('Invalid uploaded figure');
      images[id] = image;
    }
    const state = {order, notes, images, privacy:'public', reviews:[]};
    if (meta) state.meta = meta;
    return state;
  }

  globalThis.FigureSchema = Object.freeze({validateSnapshot:safeState});
})();
