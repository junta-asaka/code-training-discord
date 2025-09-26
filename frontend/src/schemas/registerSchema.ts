import { z } from "zod";

// 登録フォームのバリデーションスキーマ
export const registerSchema = z
  .object({
    name: z
      .string()
      .min(1, "ユーザー名を入力してください")
      .max(100, "ユーザー名は100文字以内で入力してください"),
    username: z
      .string()
      .min(1, "ユーザーIDを入力してください")
      .max(50, "ユーザーIDは50文字以内で入力してください")
      .regex(
        /^[a-zA-Z0-9_-]+$/,
        "ユーザーIDは英数字、アンダースコア、ハイフンのみ使用できます"
      ),
    email: z
      .string()
      .min(1, "メールアドレスを入力してください")
      .email("正しいメールアドレスを入力してください"),
    password: z
      .string()
      .min(1, "パスワードを入力してください")
      .min(8, "パスワードは8文字以上で入力してください")
      .regex(
        /^(?=.*[a-zA-Z])(?=.*\d)/,
        "パスワードは英字と数字を含む必要があります"
      ),
    confirmPassword: z.string().min(1, "パスワード確認を入力してください"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "パスワードが一致しません",
    path: ["confirmPassword"],
  });

// RegisterFormData型はregisterSchemaから自動生成
export type RegisterFormData = z.infer<typeof registerSchema>;

// APIのレスポンス型定義
export interface RegisterResponse {
  id: string;
  name: string;
  username: string;
  email: string;
  message: string;
}
