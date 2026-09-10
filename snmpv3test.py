import asyncio
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, UsmUserData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, get_cmd,
    # 认证协议常量
    usmHMACMD5AuthProtocol,
    usmHMACSHAAuthProtocol,
    usmHMAC128SHA224AuthProtocol,
    usmHMAC192SHA256AuthProtocol,
    usmHMAC256SHA384AuthProtocol,
    usmHMAC384SHA512AuthProtocol,
    # 隐私协议常量
    usmDESPrivProtocol,
    usmAesCfb128Protocol,
    usmAesBlumenthalCfb192Protocol,
    usmAesBlumenthalCfb256Protocol,
    usmAesCfb192Protocol,      # Cisco AES-192 (AES192C)
    usmAesCfb256Protocol,      # Cisco AES-256 (AES256C)
)

# ================= 协议整数映射表 =================
# 认证协议：0 MD5, 1 SHA-1, 2 SHA-224, 3 SHA-256, 4 SHA-384, 5 SHA-512
AUTH_PROTOCOLS = {
    0: usmHMACMD5AuthProtocol,
    1: usmHMACSHAAuthProtocol,
    2: usmHMAC128SHA224AuthProtocol,
    3: usmHMAC192SHA256AuthProtocol,
    4: usmHMAC256SHA384AuthProtocol,
    5: usmHMAC384SHA512AuthProtocol,
}

# 隐私协议：0 DES, 1 AES-128, 2 AES-192(标准), 3 AES-256(标准), 4 AES-192-C, 5 AES-256-C
PRIV_PROTOCOLS = {
    0: usmDESPrivProtocol,                 # DES
    1: usmAesCfb128Protocol,               # AES-128
    2: usmAesBlumenthalCfb192Protocol,     # 标准 AES-192
    3: usmAesBlumenthalCfb256Protocol,     # 标准 AES-256
    4: usmAesCfb192Protocol,               # AES-192-C (Cisco)
    5: usmAesCfb256Protocol,               # AES-256-C (Cisco)
}


def build_user_data(username, auth_key, priv_key, auth_id, priv_id):
    """根据整数 ID 构建 UsmUserData 对象"""
    auth_proto = AUTH_PROTOCOLS.get(auth_id)
    priv_proto = PRIV_PROTOCOLS.get(priv_id)
    if auth_proto is None:
        raise ValueError(f"未知的认证协议 ID: {auth_id}，有效范围 0~5")
    if priv_proto is None:
        raise ValueError(f"未知的隐私协议 ID: {priv_id}，有效范围 0~5")
    return UsmUserData(
        username,
        authKey=auth_key,
        privKey=priv_key,
        authProtocol=auth_proto,
        privProtocol=priv_proto,
    )


async def main():
    # --- 请根据你的设备信息修改以下变量 ---
    host = '192.168.0.152'
    user = 'admin123'
    auth_key = 'admin123'
    priv_key = 'admin123'
    oid = '1.3.6.1.4.1.30966.11.0.2.2.2.2.6.0'

    # 协议整数：根据设备实际配置选择
    # 认证协议：0 MD5, 1 SHA-1, 2 SHA-224, 3 SHA-256, 4 SHA-384, 5 SHA-512
    AUTH_PROTOCOL_ID = 3   # 例如 SHA-1
    # 隐私协议：0 DES, 1 AES-128, 2 AES-192(标准), 3 AES-256(标准), 4 AES-192-C, 5 AES-256-C
    PRIV_PROTOCOL_ID = 4   # 例如 AES-192-C (Cisco)
    # -------------------------------------

    try:
        user_data = build_user_data(
            user, auth_key, priv_key,
            AUTH_PROTOCOL_ID, PRIV_PROTOCOL_ID
        )
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        return

    # 注意：UdpTransportTarget.create() 是异步方法，需要用 await
    transport = await UdpTransportTarget.create((host, 161), timeout=5, retries=1)

    errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
        SnmpEngine(),
        user_data,
        transport,
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )

    if errorIndication:
        print(f"❌ 连接失败: {errorIndication}")
    elif errorStatus:
        print(f"❌ 错误状态: {errorStatus.prettyPrint()}")
    else:
        for varBind in varBinds:
            print(f"✅ 成功获取: {varBind.prettyPrint()}")


if __name__ == '__main__':
    asyncio.run(main())