import time
import logging
from collections import deque
from pymodbus.client import ModbusTcpClient

# 连接Modbus TCP服务器
client = ModbusTcpClient('192.168.1.191', port=502)
# 连接服务器



# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('device_monitor64.log'),
        logging.StreamHandler()
    ]
)

class DeviceMonitor:
    def __init__(self):
        self.fail_num = 0
        self.success_num = 0
        self.continuous_fail_count = 0
        self.last_success_time = time.time()
        self.response_times = deque(maxlen=100)  # 保存最近100次响应时间
        self.error_log = []

    def check_device_status(self):
        """检查设备状态"""
        current_time = time.time()

        # 检查是否长时间无响应（掉线）
        if current_time - self.last_success_time > 30:  # 30秒无响应视为掉线
            logging.error(f"设备掉线！超过30秒无响应")
            return "OFFLINE"

        # 检查连续失败次数
        if self.continuous_fail_count >= 5:
            logging.warning(f"设备异常！连续失败{self.continuous_fail_count}次")
            return "UNSTABLE"

        # 检查响应时间是否异常
        if len(self.response_times) > 10:
            avg_response = sum(self.response_times) / len(self.response_times)
            if avg_response > 2.0:  # 平均响应时间超过2秒
                logging.warning(f"设备响应缓慢，平均响应时间: {avg_response:.2f}s")
                return "SLOW"

        return "ONLINE"

    def record_response_time(self, duration):
        """记录响应时间"""
        self.response_times.append(duration)

    def record_error(self, error_msg, address):
        """记录错误信息"""
        error_info = {
            'time': time.strftime("%Y-%m-%d %H:%M:%S"),
            'address': address,
            'error': error_msg
        }
        self.error_log.append(error_info)
        if len(self.error_log) > 50:  # 只保留最近50条错误
            self.error_log.pop(0)

# 使用监控类
monitor = DeviceMonitor()

while True:
    conut = 0
    cycle_results = []  # 记录本周期结果

    while conut < 400:
        try:
            start_time = time.time()
            result = client.read_holding_registers(conut*100, count=100, device_id=1)
            read_duration = time.time() - start_time

            monitor.record_response_time(read_duration)

            if result and hasattr(result, 'registers'):
                monitor.success_num += 1
                monitor.continuous_fail_count = 0
                monitor.last_success_time = time.time()
                cycle_results.append(1)  # 1表示成功

                # 检查响应数据完整性
                if len(result.registers) != 100:
                    logging.warning(f"地址{conut*100}: 数据包不完整，只收到{len(result.registers)}个寄存器")
                    monitor.record_error("数据包不完整", conut*100)
                    monitor.fail_num += 1
                    monitor.continuous_fail_count += 1
                    cycle_results.append(0)  # 0表示失败

            else:
                monitor.fail_num += 1
                monitor.continuous_fail_count += 1
                cycle_results.append(0)  # 0表示失败
                monitor.record_error("读取失败", conut*100)

        except Exception as e:
            monitor.fail_num += 1
            monitor.continuous_fail_count += 1
            cycle_results.append(0)
            monitor.record_error(str(e), conut*100)
            logging.error(f"地址{conut*100}读取异常: {e}")
            client = ModbusTcpClient('192.168.1.191', port=502)


        conut += 1

        # 每读取10次检查一次设备状态
        if conut % 10 == 0:
            status = monitor.check_device_status()
            if status != "ONLINE":
                logging.info(f"当前设备状态: {status}")

    # 周期结束，生成报告
    success_rate = sum(cycle_results) / len(cycle_results) * 100 if cycle_results else 0

    print("\n" + "="*70)
    print(f"周期结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"成功率: {success_rate:.2f}%")
    print(f"设备状态: {monitor.check_device_status()}")
    print(f"累计统计 - 成功: {monitor.success_num}, 失败: {monitor.fail_num}")
    print(f"最近错误数: {len(monitor.error_log)}")
    print("="*70 + "\n")

    # 如果设备掉线，等待更长时间再重试
    if monitor.check_device_status() == "OFFLINE":
        logging.info("设备掉线，等待30秒后重试...")
        time.sleep(30)
    else:
        time.sleep(1)  # 正常循环间隔