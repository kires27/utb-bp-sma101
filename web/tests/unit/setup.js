import { eventHandler, createError } from 'h3';

globalThis.defineEventHandler = eventHandler;
globalThis.createError = createError;