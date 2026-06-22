export const categories = ["全部", "校园生活", "活动", "公告", "课程", "社团"];

export const markets = [
  {
    slug: "canteen-window",
    title: "南哪食堂本周会推出新窗口吗？",
    description: "以任一校内食堂在公告牌或窗口处实际开始售卖新菜系为准。",
    category: "校园生活",
    yes: 63,
    volume: "128.40 NWC",
    closeLabel: "3 天后截止",
    closeTime: "2026-06-24 20:00",
    criteria: "窗口完成挂牌并连续开放两个餐时，即判定为 YES。",
    participants: 42,
    trend: [48, 51, 55, 58, 61, 60, 63],
  },
  {
    slug: "night-run-300",
    title: "下一次社团夜跑报名会超过 300 人吗？",
    description: "以社团公开报名表或活动群公告的最终报名人数为准。",
    category: "活动",
    yes: 41,
    volume: "76.25 NWC",
    closeLabel: "今晚截止",
    closeTime: "2026-06-21 23:00",
    criteria: "报名人数大于 300 判定为 YES，等于或低于 300 判定为 NO。",
    participants: 28,
    trend: [52, 48, 44, 43, 39, 40, 41],
  },
  {
    slug: "library-late-close",
    title: "本月图书馆闭馆时间会临时延后吗？",
    description: "观察本月内图书馆是否发布临时延后闭馆的正式通知。",
    category: "公告",
    yes: 54,
    volume: "94.10 NWC",
    closeLabel: "12 天后截止",
    closeTime: "2026-06-30 18:00",
    criteria: "只统计临时通知，不统计既定节假日或考试周安排。",
    participants: 35,
    trend: [45, 47, 49, 52, 50, 53, 54],
  },
  {
    slug: "compiler-quiz",
    title: "编译原理小测平均分会超过 82 分吗？",
    description: "以课程群公布的全班平均分为准，四舍五入前原始均分超过 82 即为 YES。",
    category: "课程",
    yes: 57,
    volume: "63.80 NWC",
    closeLabel: "5 天后截止",
    closeTime: "2026-06-26 12:00",
    criteria: "若老师未公布平均分，事件进入申诉窗口由管理员裁定。",
    participants: 21,
    trend: [61, 59, 56, 58, 55, 56, 57],
  },
];

export const positions = [
  { market: markets[0].title, side: "YES", stake: "3.00 NWC", estimate: "4.72 NWC" },
  { market: markets[1].title, side: "NO", stake: "2.50 NWC", estimate: "4.24 NWC" },
  { market: markets[2].title, side: "YES", stake: "1.00 NWC", estimate: "1.85 NWC" },
];

export const ledger = [
  { kind: "注册赠送", amount: "+10.00", ref: "system", time: "06-21 09:18" },
  { kind: "每日签到", amount: "+1.00", ref: "system", time: "06-21 09:22" },
  { kind: "买入 YES", amount: "-3.00", ref: "食堂新窗口", time: "06-21 10:04" },
  { kind: "买入 NO", amount: "-2.50", ref: "夜跑报名", time: "06-21 10:16" },
];

export const adminQueue = [
  { title: "校车晚班本周会新增一班吗？", submitter: "251502013", category: "公告" },
  { title: "周末草坪电影会因雨取消吗？", submitter: "241000001", category: "活动" },
];

export const forumPosts = [
  {
    slug: "market-making-notes",
    title: "平价彩池和订单簿相比，机器人策略该怎么写？",
    author: "251502013",
    replies: 8,
    views: 142,
    time: "12 分钟前",
    excerpt: "没有挂单和撤单之后，策略重点从报价变成了资金分配和事件筛选。",
  },
  {
    slug: "event-criteria",
    title: "事件判定标准怎么写才不容易吵起来？",
    author: "230000007",
    replies: 15,
    views: 231,
    time: "1 小时前",
    excerpt: "建议标题只问一个二元问题，描述里写清楚数据源和截止口径。",
  },
  {
    slug: "nwc-daily-checkin",
    title: "每日签到的 NWC 应该攒着还是用来练手？",
    author: "241502099",
    replies: 5,
    views: 88,
    time: "今天 09:40",
    excerpt: "小额下注更适合熟悉赔率变化，别把所有 NWC 压在一个事件上。",
  },
];
