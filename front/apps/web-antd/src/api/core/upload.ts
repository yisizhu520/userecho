/**
 * 通用上传 API
 */

import { requestClient } from '#/api/request';

/** 上传类型 */
export type UploadType = 'screenshot' | 'avatar' | 'document' | 'attachment';

/** 上传签名请求 */
export interface UploadSignRequest {
  filename: string;
  upload_type: UploadType;
  content_type?: string;
}

/** 上传签名响应 */
export interface UploadSignResponse {
  upload_url: string;
  method: 'PUT';
  headers: Record<string, string>;
  cdn_url: string;
  object_key: string;
  expires_in: number;
}

/**
 * 获取上传签名
 */
export async function getUploadSign(data: UploadSignRequest) {
  return requestClient.post<UploadSignResponse>('/api/v1/app/upload/sign', data);
}

/**
 * 直传到对象存储
 */
export async function uploadToSignedUrl(sign: UploadSignResponse, file: File) {
  const headers = new Headers(sign.headers || {});
  if (!headers.has('Content-Type') && file.type) {
    headers.set('Content-Type', file.type);
  }

  const response = await fetch(sign.upload_url, {
    method: sign.method || 'PUT',
    headers,
    body: file,
  });

  if (!response.ok) {
    throw new Error(`直传失败: ${response.status}`);
  }
}

/**
 * 完整上传流程（获取签名 + 直传）
 */
export async function uploadFile(file: File, uploadType: UploadType): Promise<string> {
  const sign = await getUploadSign({
    filename: file.name,
    upload_type: uploadType,
    content_type: file.type,
  });

  await uploadToSignedUrl(sign, file);

  return sign.cdn_url;
}

/**
 * 上传截图（便捷方法）
 */
export async function uploadScreenshot(file: File): Promise<string> {
  return uploadFile(file, 'screenshot');
}

/**
 * 上传头像（便捷方法）
 */
export async function uploadAvatar(file: File): Promise<string> {
  return uploadFile(file, 'avatar');
}

/**
 * 上传文档（便捷方法）
 */
export async function uploadDocument(file: File): Promise<string> {
  return uploadFile(file, 'document');
}

/**
 * 上传附件（便捷方法）
 */
export async function uploadAttachment(file: File): Promise<string> {
  return uploadFile(file, 'attachment');
}
