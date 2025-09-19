import { z } from 'zod';

// ログインフォームのバリデーションスキーマ
// z: 型安全なスキーマ定義とバリデーションを提供するライブラリ
export const loginSchema = z.object({
  username: z
    .string()
    .min(1, 'ユーザー名を入力してください')
    .max(50, 'ユーザー名は50文字以内で入力してください'),
  password: z
    .string()
    .min(1, 'パスワードを入力してください')
    .min(8, 'パスワードは8文字以上で入力してください'),
});

// LoginFormData型はloginSchemaから自動生成
export type LoginFormData = z.infer<typeof loginSchema>;

// APIのレスポンス型定義
export interface LoginResponse {
  id: string;
  name: string;
  username: string;
  access_token: string;
  token_type: string;
  next?: string;
}
