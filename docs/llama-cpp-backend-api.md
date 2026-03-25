## API

### 公共变量

```http
@baseUrl = http://192.168.1.2:18085
@auth = Authorization: Bearer gb6haanmGGck4TCPQKWAfuuCDzfBQYQw
```

### /health 健康检查

```http
GET {{baseUrl}}/health HTTP/1.1
content-type: application/json
{{auth}}
```

```json
{
  "status": "ok"
}
```

### 获取llama-server的metrics信息

```http
GET {{baseUrl}}/metrics HTTP/1.1
content-type: application/text-plain
{{auth}}
```

### /tokenize 分词

```http
POST {{baseUrl}}/tokenize HTTP/1.1
content-type: application/json
{{auth}}

{
    "content": "你好，世界！"
}
```

```json
{"tokens":[109377,3837,99011,6313]}
```

### /apply-template 应用模板

```http
POST {{baseUrl}}/apply-template HTTP/1.1
content-type: application/json
{{auth}}

{
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": "你好，世界！"
        }
      ]
}
```

### /completion 补全

```http
POST {{baseUrl}}/completion HTTP/1.1
content-type: application/json
{{auth}}

{
    "prompt": "[gMASK]<sop><|system|>You are a helpful assistant.<|user|>你好，世界！<|assistant|><think></think>你好，世界！<|user|>你叫什么名字？<|assistant|><think></think>",
    "max_tokens": 10,
    "temperature": 0.7,
    "id_slot": 0
}
```

### /props 获取模型属性

```http
GET {{baseUrl}}/props HTTP/1.1
content-type: application/json
{{auth}}
```

### /slots 获取所有插槽

```http
GET {{baseUrl}}/slots HTTP/1.1
content-type: application/json
{{auth}}
```

### /slots?{n}?action=save 保存插槽

```http
POST {{baseUrl}}/slots/1?action=save HTTP/1.1
content-type: application/json
{{auth}}

{
    "filename": "slot1.bin"
}
```
