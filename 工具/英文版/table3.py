# 11-09 英文版文字表（三）：拆开显示的目标、计策、被封
T = {
'冲阵一次都没撞上城': 'No charger reaches the wall', '城防都剩一半以上': 'Wall above half', '打完所有敌人，城防不破': 'Defeat all foes, wall holds',
'我方城防（就是你们的血）都剩一半以上': 'Your wall (your HP) above half', '斩了敌将，我方城防（就是你们的血）不破': 'Slay the general, your wall (your HP) holds',
'把草营全烧掉': 'burn every tent', '张宝 · 急行': 'Zhang Bao · Forced March', '急行': 'Forced March', '敌军快三成，10 秒': 'Enemies 30% faster for 10s',
'刘备的招式被封 # 秒': 'Liu Bei sealed #s', '张飞的招式被封 # 秒': 'Zhang Fei sealed #s',
'两星之上，再把草营全烧掉': '2★ plus burn every tent', '城防都剩一半以上（剩 #%）': 'Wall above half (now #%)',
}
T.update({   # 印章上的字：英文整个词放一格，越短越好
'毕': '✓', '升': '▲', '令': '!', '资': 'M', '月': 'P', '功': '★', '首': '1st', '随': 'Adv', '选': 'Pick', '连携': 'Combo', '荐': 'Tip', '已领': '✓',
'十一': '11', '十二': '12', '十三': '13', '十四': '14', '十五': '15', '十六': '16', '十七': '17', '十八': '18', '十九': '19', '二十': '20',
})
T.update({
' · 今日军务 # 道': ' · # daily orders', '双剑破阵': 'Twin Blade Breach', '反击 # 秒 · 招式伤害 +#%': 'Counter #s · skill dmg +#%', '场上黄巾回三成血': 'All Turbans heal 30%',
'张宝 · 妖术回春': 'Zhang Bao · Healing Hex', '妖术回春': 'Healing Hex', '无双·喝断它': 'Peerless — Roar it!', '晕而斩之': 'Stun & Slay', '喝而斩之': 'Roar & Slay', '桃园同心': 'Peach Garden Bond', '横竖斩': 'Cross Cut',
'杂': 'Misc', '灼烧': 'Burn', '点卯': 'Roll Call', '补': '+', '金': 'Gold', '黄巾渠帅': 'Turban Chief',
'着火的敌人走过草棚会把草棚点着，火顺着草棚一路烧过去': 'Burning foes ignite the straw huts they pass — the fire spreads hut to hut',
})
T.update({   # 军务后半句、官阶、晋阶奖励、神兵
'拿三星': 'get 3★', '漏兵不超过两个': 'let 2 or fewer through', '城防剩九成以上': 'wall above 90%', '让关羽伤害第一': 'Guan Yu tops damage', '让张飞伤害第一': 'Zhang Fei tops damage', '让刘备伤害第一': 'Liu Bei tops damage',
'晋升时拿一个连携战法': 'take a combo tactic on promotion', '救下九成百姓': 'save 90% of civilians', '一喝喝断一次无双': 'Roar-break Peerless once', '一喝喝断两次无双': 'Roar-break Peerless twice',
'车驾保住八成': 'keep the carriage above 80%', '冲车保住一半撞开关门': 'keep the ram above half and breach the gate', '两星之上，再车驾保住八成': '2★ plus carriage above 80%',
'城防和车驾都剩一半以上': 'Wall and carriage above half',
'青龙鳞': 'Dragon Scale', '蛇纹镔铁': 'Serpent Steel', '雌雄剑胚': 'Twin Sword Blank', '陨铁': 'Meteor Iron', '将印': 'General\'s Seal', '体力': 'Stamina', '机缘': 'Fortune', '资历': 'Merit',
'义军队正': 'Volunteer Sergeant', '讨贼队正': 'Rebel-Hunter Sergeant', '讨贼副尉': 'Deputy Commandant', '讨贼正尉': 'Commandant', '校尉': 'Colonel', '别部司马': 'Detached Commander', '徐州牧': 'Governor of Xuzhou', '左将军': 'General of the Left',
'三人各一招': 'One skill each', '换上第一套新甲': 'New armor I', '换上第二套新甲': 'New armor II', '换上第三套新甲': 'New armor III', '招式二阶资格': 'Tier-2 skills', '招式三阶资格': 'Tier-3 skills',
'张飞新招「丈八破阵」': 'Zhang Fei: "Serpent Spear"', '关羽新招「温酒斩将」': 'Guan Yu: "Wine Still Warm"', '刘备新招「仁德护阵」': 'Liu Bei: "Benevolent Guard"',
'被动第一格': 'Passive slot 1', '被动第二格': 'Passive slot 2', '被动一格': 'Passive slot', '第一章成长上限': 'Chapter 1 growth cap',
'丈八蛇矛': 'Serpent Spear', '兵器': 'Weapons', '双股剑 · 剑印': 'Twin Blades · Sword Seal', '当阳一喝 · 怒雷': 'Roar · Wrath', '剑印 · 终阶': 'Sword Seal · Final', '觉醒': 'Awaken',
'砍中的定住 4 秒：走不动、放不了箭、施不了法': 'Hits freeze foes for 4s: no moving, shooting or casting',
'扫过的 4 秒内盾和甲都失效、多受 20%': 'Swept foes lose shields & armor for 4s, take 20% more',
'喝完城前留一道火沟烧 4 秒：走进去着火、慢一半，骑兵落马': 'Leaves a 4s fire trench: foes catch fire, slow by half, cavalry unhorsed',
'定住 6 秒、双股剑多两剑：追百姓的兵被定住': 'Freeze 6s, Twin Blades strike twice more; civilian-chasers frozen',
'选一人觉醒：招式伤害 +20%、冷却 -15%': 'Awaken one hero: skill dmg +20%, cooldown -15%',
'张飞普攻、招式 #%': 'Zhang Fei attacks & skills #%', '刘备普攻、招式 #%': 'Liu Bei attacks & skills #%', '普攻、招式 #%': 'Attacks & skills #%',
})
T.update({'孟德献刀': 'Cao Cao\'s Dagger', '白身。': 'No rank.'})
T.update({'限时': 'Timed', '累计 # 颗星、首通 · 张角': '# stars total, first clear · Zhang Jiao'})
T.update({'打赢一次（掉青龙鳞）': 'win once (drops Dragon Scale)', '打赢一次（掉蛇纹镔铁）': 'win once (drops Serpent Steel)', '打赢一次（掉雌雄剑胚）': 'win once (drops Twin Sword Blank)', '打赢一次（掉陨铁）': 'win once (drops Meteor Iron)'})
