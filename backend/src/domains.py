import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.schema import CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# モデル: ユーザー
class User(Base):
    __tablename__ = "users"

    # ID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # 表示名
    name = Column(String, nullable=False)
    # ユーザー名
    username = Column(String, unique=True, nullable=False)
    # メールアドレス
    email = Column(String, unique=True, nullable=False)
    # パスワードハッシュ
    password_hash = Column(String, nullable=False)
    # 説明
    description = Column(String, nullable=True)
    # 削除日時
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    # 作成日時
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # 更新日時
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),  # デフォルト値を現在時刻に設定
        onupdate=func.now(),  # レコード更新時に現在時刻に更新
        nullable=False,
    )


# モデル: セッション
class Session(Base):
    __tablename__ = "sessions"

    # ID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # ユーザーID
    # 外部キー: users.id
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # アクセストークンハッシュ（短期間有効）
    access_token_hash = Column(String, unique=True, nullable=False)
    # リフレッシュトークンハッシュ（長期間有効）
    refresh_token_hash = Column(String, unique=True, nullable=False)
    # ユーザーエージェント
    user_agent = Column(String, nullable=True)
    # IPアドレス
    ip_address = Column(String, nullable=True)
    # 失効日時
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    # 作成日時
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # アクセストークン有効期限
    access_token_expires_at = Column(DateTime(timezone=True), nullable=False)
    # リフレッシュトークン有効期限
    refresh_token_expires_at = Column(DateTime(timezone=True), nullable=False)


# モデル: フレンド
class Friend(Base):
    __tablename__ = "friends"
    # 複合ユニーク制約の設定
    __table_args__ = (
        UniqueConstraint("user_id", "related_user_id"),
        # 自己参照防止
        CheckConstraint("user_id != related_user_id", name="check_no_self_friend"),
    )

    # ID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # ユーザーID
    # 外部キー: users.id
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # 相手ユーザーID
    # 外部キー: users.id
    related_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # タイプ
    type = Column(String, nullable=False)
    # 作成日時
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# モデル: チャネル
class Channel(Base):
    __tablename__ = "channels"

    # ID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # サーバーID
    guild_id = Column(UUID(as_uuid=True), ForeignKey("guilds.id"), nullable=True)
    # 相手サーバーID（DMチャネルのみ）
    related_guild_id = Column(
        UUID(as_uuid=True), ForeignKey("guilds.id"), nullable=True
    )
    # タイプ
    type = Column(String, nullable=False, default="text")
    # チャネル名
    name = Column(String, nullable=True, default="")
    # 管理者ユーザーID
    # 外部キー: users.id
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # 最終メッセージID
    # 外部キー: messages.id
    last_message_id = Column(
        UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True
    )
    # 削除日時
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    # 作成日時
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # 更新日時
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),  # デフォルト値を現在時刻に設定
        onupdate=func.now(),  # レコード更新時に現在時刻に更新
        nullable=False,
    )


# モデル: メッセージ
class Message(Base):
    __tablename__ = "messages"

    # ID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # チャネルID
    # 外部キー: channels.id
    channel_id = Column(
        UUID(as_uuid=True),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
    )
    # 作成者ユーザID
    # 外部キー: users.id
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # タイプ
    type = Column(String, nullable=False)
    # 内容
    content = Column(String, nullable=True)
    # 返信先メッセージID
    # 外部キー: messages.id
    referenced_message_id = Column(
        UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True
    )
    # 削除日時
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    # 作成日時
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # 更新日時
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),  # デフォルト値を現在時刻に設定
        onupdate=func.now(),  # レコード更新時に現在時刻に更新
        nullable=False,
    )


# モデル: ギルド
class Guild(Base):
    __tablename__ = "guilds"

    # ID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # ギルド名
    name = Column(String, nullable=False, default="@me")
    # 管理者ユーザーID
    # 外部キー: users.id
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # 削除日時
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    # 作成日時
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # 更新日時
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),  # デフォルト値を現在時刻に設定
        onupdate=func.now(),  # レコード更新時に現在時刻に更新
        nullable=False,
    )


# モデル: ギルドメンバー
class GuildMember(Base):
    __tablename__ = "guild_members"
    # 複合ユニーク制約の設定
    __table_args__ = (UniqueConstraint("guild_id", "user_id"),)

    # ID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # ギルドID
    # 外部キー: guilds.id
    guild_id = Column(UUID(as_uuid=True), ForeignKey("guilds.id"), nullable=False)
    # ユーザーID
    # 外部キー: users.id
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    # 役職
    role = Column(String, nullable=False, default="member")
