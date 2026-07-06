import argparse
import sys

from core.database import init_db, SessionLocal
from core.crud import create_user, get_password_hash, get_user_by_email
from model.roles import UserRole


def parse_args():
    parser = argparse.ArgumentParser(
        description='Create or promote an admin user in the Student Management API database.'
    )

    parser.add_argument(
        '--name',
        required=True,
        help='Full name of the admin user.'
    )
    parser.add_argument(
        '--email',
        required=True,
        help='Email address for the admin user.'
    )
    parser.add_argument(
        '--password',
        required=True,
        help='Password for the admin user.'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Promote an existing user to admin and update the password if the email already exists.'
    )

    return parser.parse_args()


def main():
    args = parse_args()
    email = args.email.strip().lower()
    password = args.password

    init_db()

    db = SessionLocal()
    try:
        existing_user = get_user_by_email(db, email)

        if existing_user is not None:
            if existing_user.role == UserRole.ADMIN:
                print(f'Admin user already exists for email: {email}')
                return 0

            if not args.force:
                print(
                    'User already exists with this email but is not an admin. '
                    'Use --force to promote the existing user to admin.'
                )
                return 1

            existing_user.role = UserRole.ADMIN
            existing_user.name = args.name
            existing_user.password = get_password_hash(password)
            db.commit()
            print(f'Existing user promoted to admin: {email}')
            return 0

        admin = create_user(
            db,
            args.name,
            email,
            password,
            role='admin'
        )

        print(f'Admin user created: {admin.email} (id={admin.id})')
        return 0

    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())
