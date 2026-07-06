from fastapi import Depends,HTTPException
from  .user_dependecies import get_current_user
def role_required(allowed_roles: list):

    def checker(user=Depends(get_current_user)):

        if user["role"] not in allowed_roles:

            raise HTTPException(
                status_code=403,
                detail="Access Denied"
            )

        return user

    return checker