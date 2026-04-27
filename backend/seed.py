from app.core.security import hash_password
import asyncio
import csv
import uuid
from pathlib import Path
from sqlalchemy import select, insert, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.database import async_session
from app.models.role import Role, user_roles
from app.models.user import User

DATA_DIR = Path(__file__).parent / "data"


async def seed():
    async with async_session() as session:

        # роли
        print("Заполняем роли...")
        with open(DATA_DIR / "roles.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                role_id = uuid.UUID(row["id_роли"])
                existing = await session.execute(
                    select(Role).where(Role.id == role_id)
                )
                if not existing.scalar_one_or_none():
                    role = Role(
                        id=role_id,
                        name=row["наименование_роли"].strip(),
                    )
                    session.add(role)
                    print(f"  + Роль: {row['наименование_роли']}")
                else:
                    print(f"  = Роль уже есть: {row['наименование_роли']}")

        await session.commit()

        # пользаки
        print("\nЗаполняем пользователей...")

        # Читаем CSV и группируем по пользователю
        users_dict: dict[str, dict] = {}  # ключ - логин

        with open(DATA_DIR / "users.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                user_id = uuid.UUID(row["id_пользователя"])
                role_id = uuid.UUID(row["id_роли"])
                username = row["логин"].strip()

                if username not in users_dict:
                    users_dict[username] = {
                        "id": user_id,
                        "username": username,
                        "hashed_password": row["хэш_пароля"].strip(),
                        "full_name": row["ФИО"].strip(),
                        "is_active": row["статус_активности"].strip().lower() == "активен",
                        "role_ids": [role_id],
                    }
                else:
                    users_dict[username]["role_ids"].append(role_id)

        # Сохраняем пользователей
        for user_data in users_dict.values():
            existing = await session.execute(
                select(User).where(User.id == user_data["id"])
            )
            user = existing.scalar_one_or_none()

            if not user:
                user = User(
                    id=user_data["id"],
                    username=user_data["username"],
                    hashed_password=hash_password("Test12345!"),
                    full_name=user_data["full_name"],
                    is_active=user_data["is_active"],
                )
                session.add(user)
                await session.flush()
                print(f"  + Пользователь: {user_data['username']}")
            else:
                print(f"  = Пользователь уже есть: {user_data['username']}")

            # Удаляем старые роли пользователя
            await session.execute(
                delete(user_roles).where(user_roles.c.user_id == user_data["id"])
            )

            # Добавляем роли напрямую через промежуточную таблицу
            for role_id in user_data["role_ids"]:
                await session.execute(
                    insert(user_roles).values(
                        user_id=user_data["id"],
                        role_id=role_id,
                    )
                )
                print(f"    → роль привязана: {role_id}")

        await session.commit()
        print("\nТестовые данные загружены успешно")

if __name__ == "__main__":
    asyncio.run(seed())