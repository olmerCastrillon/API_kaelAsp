from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
my_pass="Oca80Lag"
password_cifrada = pwd_context.hash(my_pass[:70])
print(password_cifrada)

