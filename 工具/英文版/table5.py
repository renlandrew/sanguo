# -*- coding: utf-8 -*-
# 11-10 英文版文字表（五）：神兵页。用户手机上玩英文正式版，截图里「下一级 · 精钢 +2」「凡铁 +1」还是中文：「还有不少中文，继续坚持」
T = {
'雌雄双股剑': 'Twin Swords of Fate',
'精钢': 'Fine Steel', '龙纹': 'Dragon Vein', '鎏金': 'Gilded', '绝世': 'Matchless', '玄铁': 'Dark Iron',
'寒霜': 'Frost', '赤焰': 'Crimson Flame', '紫电': 'Violet Bolt', '天命': 'Mandate',
'下一级': 'Next', '锤': 'Hit',
'已是天命神兵': 'Already a Mandate weapon', '已是绝世神兵': 'Already a Matchless weapon',
'兵器可炼到': 'Weapons refine up to', '打完第一章': 'finish Chapter 1', '晋阶校尉': 'promote to Colonel',
'打完第一章后可以继续精炼': 'Finish Chapter 1 to refine further', '晋阶校尉后可以继续精炼': 'Promote to Colonel to refine further',
'已炼到这一阶的上限 +#': 'Refined to this tier\'s cap, +$1',
'陨铁 # 换 1': '$1 Meteor Iron for 1',
'功绩也给，兵器 +6 起要': 'Deeds grant it too; weapons need it from +6',
'破题门槛': 'Requirement', '材料够了，去军帐打造、研习就能打': 'Materials ready — forge and study at the Camp, then fight', '去军帐': 'To Camp',
}
# 兵器阶名带等级的三种写法：「精钢 +2」「精钢 · +2」「下一级 · 精钢 +2」。「神兵」单独出现时是页名 Armory，带等级时是阶名 Divine
for zh, en in [('凡铁', 'Plain Iron'), ('精钢', 'Fine Steel'), ('龙纹', 'Dragon Vein'), ('鎏金', 'Gilded'), ('神兵', 'Divine'), ('绝世', 'Matchless'),
               ('玄铁', 'Dark Iron'), ('寒霜', 'Frost'), ('赤焰', 'Crimson Flame'), ('紫电', 'Violet Bolt'), ('天命', 'Mandate')]:
    T[zh + ' +#'] = en + ' +$1'
    T[zh + ' · +#'] = en + ' · +$1'
    T['下一级 · ' + zh + ' +#'] = 'Next · ' + en + ' +$1'
