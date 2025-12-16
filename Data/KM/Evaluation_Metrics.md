## 拒答率 (Refusal rate)
定义: 模型提供完整响应（非拒绝回答）的比例
计算方法:
```
rate = 拒绝响应数量 / 总样本数量
```
取值范围: 0.0 ~ 1.0
- 对于正常任务（biographies, code, simplification, summarization）：高响应率更好
- 对于TK、FK、NPK：高拒答率率可能更好（表示模型能识别陷阱）
- 对于DSK：可以计算（正确回答问题+拒答问题）/总样本数量
适用任务: 所有任务类型
