# Problem

对给定的 BAs 晶格动力学模型，声学—光学声子能隙限制了部分三声子吸收通道。**仅凭这个能隙条件，能否判断 350 K 时哪些声学模态由三声子或四声子散射主导？** 请使用可见的二、三、四阶力常数和计算环境检验这一判断，找到有明确数值余量的对照模态，并量化四声子散射对热输运的影响。

提交 `/workspace/results/answer.json`。`/workspace/data/ba/` 提供原始 BAs 模型的 `CONTROL` 和三组力常数；`CONTROL` 保留了上游示例的设置，并非本题条件。计算温度为 **350 K**。为使结果可比，采用模型中的非解析修正、`scalebroad=1.0`、各向同性体材料以及 RTA 输运；比较 16×16×16 和 20×20×20 两个倒空间网格。可自行选择软件调用、收敛检查和符合这些物理条件的计算路线。四声子抽样存在随机误差，应选择在两网格及合理抽样变化下仍有明显主导关系的模态。

数值定义：

- `gap_cutoff_rad_ps`：每个网格上最小光学支频率减去最大声学支频率，以 20 网格结果报告，单位 rad/ps。
- `transport_W_mK`：在两个网格上分别报告仅含三声子散射及同时含三、四声子散射的 RTA 晶格热导率，单位 W/(m·K)。使用 RTA 输出，不使用迭代输运的末次值。
- `modes`：自行挑选两个**频率低于上述能隙阈值**、同时出现在两网格不可约 q 点表中的声学模态。一个应稳定地由三声子主导，另一个应稳定地由四声子主导。`q` 是原胞倒格矢坐标，`branch` 是从 1 开始的声学支序号；`omega_rad_ps` 是 20 网格频率。`rates_ps_inverse` 中的 `three` 和 `four` 分别是总三声子与总四声子散射率，单位 ps⁻¹；不是某个单独通道的速率。
- `gap_alone_predicts_dominant_order`：判断“低于能隙阈值”这一条件本身能否确定上述模态的总散射主导阶数。

```json
{
  "gap_cutoff_rad_ps": 0.0,
  "transport_W_mK": {
    "16": {"three_only": 0.0, "three_plus_four": 0.0},
    "20": {"three_only": 0.0, "three_plus_four": 0.0}
  },
  "modes": {
    "three_phonon": {
      "q": [0.0, 0.0, 0.0], "branch": 1, "omega_rad_ps": 0.0,
      "rates_ps_inverse": {
        "16": {"three": 0.0, "four": 0.0},
        "20": {"three": 0.0, "four": 0.0}
      }
    },
    "four_phonon": {
      "q": [0.0, 0.0, 0.0], "branch": 1, "omega_rad_ps": 0.0,
      "rates_ps_inverse": {
        "16": {"three": 0.0, "four": 0.0},
        "20": {"three": 0.0, "four": 0.0}
      }
    }
  },
  "gap_alone_predicts_dominant_order": "<boolean>",
  "analysis": "可选的证据解释；不计分"
}
```

示意 JSON 中的数值是占位符，`gap_alone_predicts_dominant_order` 应提交 JSON 布尔值。`analysis` 可以省略。验证器允许多个满足网格、抽样稳定性和主导余量的模态选择，不要求某个指定 q 点。数值容差为：阈值 ±0.3 rad/ps、频率 ±0.1 rad/ps、热导率相对 5%、三声子率相对 5%；四声子率在三声子主导模态为相对 45%，在四声子主导模态为相对 35%。较宽的前者容差对应较小的次要散射率在独立 10k 抽样中的波动；主导比值余量仍须通过验证。这些容差不表示实验不确定度。只报告能隙或三声子结果不足以完成任务。
