from RandomParcelsGenerator import RandomParcelsGenerator
from Configuration import SeparateConfig
from Sim import Sim
import sys
import signal


def disable_ctrl_c(a, b):
    pass


if __name__ == '__main__':
    # 禁用ctrl+c
    signal.signal(signal.SIGINT, disable_ctrl_c)
    if len(sys.argv) < 2:
        print('Args Error! Usage: start_scripts [config_path]')
        sys.exit()
    config_path = sys.argv[1]
    config = SeparateConfig(yml_path=config_path)
    sim = Sim(generator=RandomParcelsGenerator(config), sim_config=config)
    sim.run()
