from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]
p=json.loads((root/'analysis/round1_plan.json').read_text(encoding='utf-8'))
a,b=p['products']; g=p['global']
rows=[('产品槽',a['slot'],b['slot']),('产品名',a['name'],b['name']),('欧洲市场','选中','选中'),('亚洲市场','不选','不选'),
      ('外观',a['style'],b['style']),('性能',a['performance'],b['performance']),('电池寿命',a['battery'],b['battery'])]
labels={'camera':'相机','storage':'额外存储','screen':'高级屏幕','navigation':'高精度导航模块','security':'指纹加密'}
for key,label in labels.items(): rows.append((label,*['选中' if v['features'][key] else '不选' for v in [a,b]]))
rows.append(('欧洲价格，欧元',a['price'],b['price']))
segments=['普通消费者','高端消费者','企业用户','高端企业用户']
for key,unit in [('quantity','预测，千台'),('ads','广告，千欧元')]:
    for i,label in enumerate(segments): rows.append((label+unit,a[key][i],b[key][i]))
for i,label in enumerate(['品牌专卖店','家电卖场','百货商场']): rows.append((label+'，千欧元',a['channels'][i],b['channels'][i]))
table='\n'.join(f'| {name} | {x} | {y} | □ |' for name,x,y in rows)
text=f'''# 第一回合录入与回读清单

版本 {p['version']}，主方案。操作人________；复核人________；小组保存时间________。

本表用于执行，依据和备用方案见 [完整决策方案](final-round1-plan.md)。若主配置报价未通过，请切换该文的完整备用方案，不混用不同版本的价格和预测。

截止2026年10月17日22:00；市场14；维维一笑队；正式回合1。先在指定操作者个人区录入，最后保存到小组并回读。槽2由原亚洲1改为欧洲2，槽3—6全部不选市场。

| 字段 | 欧洲1 | 欧洲2 | 小组回读 |
|---|---:|---:|---|
{table}

| 全公司字段 | 输入或动作 | 小组回读 |
|---|---|---|
| 性能研发，千欧元 | {g['rd_performance']} | □ |
| 电池研发，千欧元 | {g['rd_battery']} | □ |
| 额外质保 | {g['extra_warranty_months']}个月 | □ |
| 维修质量投资，千欧元 | {g['repair_quality']} | □ |
| 欧洲维修成本加成 | {g['repair_markup_pct']['EU']}% | □ |
| 亚洲维修成本加成 | {g['repair_markup_pct']['AS']}% | □ |
| 欧洲维修销量预测，若可填 | {g['repair_quantity']['EU']}千件 | □ |
| 亚洲维修销量预测，若可填 | {g['repair_quantity']['AS']}千件 | □ |
| 付款期限 | {p['assumptions']['payment_days']}天 | □ |
| 欧洲／亚洲报告 | 各保留购买；按实际可用开关及收费核验 | □ |
| 亚洲手机业务 | 无在售产品、无有效广告及渠道费用 | □ |
| 槽3—6 | 两地区均未启用 | □ |

## 报价及预算核验

| 项目 | 主方案要求或核对值 | 实际记录 |
|---|---|---|
| 欧洲1单位成本＋质保 | ≤280欧元 | ________ |
| 欧洲2单位成本 | ≤240欧元 | ________ |
| 欧洲2单位质保现值 | ≤5欧元 | ________ |
| 两产品技术利用率 | 各≤100%，配置已保存 | ________ |
| 欧洲1／欧洲2总预测 | 65／60千台 | ________ |
| 产品收入 | 54425千欧元 | ________ |
| 管理费 | 7000千欧元 | ________ |
| 生产线 | 4400千欧元 | ________ |
| 广告／渠道／研发 | 1900／1900／4000千欧元 | ________ |
| 报告 | 两份合计1200，或记录购买限制 | ________ |
| 净利润／现金／贷款 | 记录平台值，不以预算利润证明需求 | ________ |
| 小组保存及回读 | 回读所有字段，不仅比较利润 | ________ |

最终采用：□主方案 □低电池备用 □单产品备用 □团队修订（附变更记录）。

微调记录：时间________ 操作人________ 字段________ 原值________ 新值________ 理由________ 重新核验________。

留存小组清单、产品报价、损益表、资产负债表、保存时间截图。最迟21:50完成保存和回读，保留最后10分钟处理录入或网络问题。
'''
(root/'current/round1-entry-checklist.md').write_text(text,encoding='utf-8')
print('Built checklist from',p['version'],'with',len(rows),'product rows.')
