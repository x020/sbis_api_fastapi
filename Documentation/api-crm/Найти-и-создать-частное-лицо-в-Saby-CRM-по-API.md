# Найти и создать частное лицо в Saby CRM по API

Прежде чем создавать частное лицо в Saby CRM, убедитесь что такого еще нет в системе. Затем создайте новую карточку. Выполните запрос.

## Найти частное лицо в Saby

## Создать частное лицо в Saby

## Параметры запроса

Метод запроса: CRMClients.GetCustomerByParams

Адрес запроса: https://online.sbis.ru/service/

| Параметр | Тип | Описание |
|----------|-----|----------|
| CustomerID | integer | Идентификатор клиента в локальной схеме |
| UUID | uuid | Идентификатор клиента в сервисе профилей |
| ExternalId | text | Внешний идентификатор Контрагента |
| INN | text | ИНН |
| SNILS | text | СНИЛС |
| ContactData | recordSet | Набор записей формата таблицы «Contact» |
| FirstName | text | Имя |
| LastName | text | Фамилия |
| SecondName | text | Отчество |

## Примеры

### Найти частное лицо по ФИО

```javascript
requirejs(['Types/source'], function(blo){
new blo.SbisService({
    endpoint: {
        contract: 'CRMClients',
        address: '/service/?x_version=20.7202-3'
    }
}).call(
'GetCustomerByParams',
{
    "client_data": {
        "d": [
            "Иванов",
            "Иван",
            "Иванович",
            267
        ],
        "s": [
            {
                "n": "Surname",
                "t": "Строка"
            },
            {
                "n": "Name",
                "t": "Строка"
            },
            {
                "n": "Patronymic",
                "t": "Строка"
            },
            {
                "n": "CustomerID",
                "t": "Число целое"
            }      
        ],
        "_type": "record",
        "f": 0
    },
    "options": null
}
); //.addBoth(console.info);
});
```

### Найти частное лицо по номеру телефона, в формате *.php

```php
<?php
         
$method = 'CRMClients.GetCustomerByParams';
$url = 'https://online.sbis.ru/service/?x_version=22.3100-709&x_version=22.2134-244';
// Array for data
$dataArray = [
    ['89151111111', 'mobile_phone', null]
];

$data = [
    'jsonrpc' => '2.0',
    'protocol' => 6,
    'method' => $method,
    'params' => [
        'client_data' =>
        [
            'd' => [
                [
                    'd' => $dataArray,
                    's' => [
                        ['t' => 'Строка', 'n' => 'Value'],
                        ['t' => 'Строка', 'n' => 'Type'],
                        ['t' => 'Строка', 'n' => 'Priority']
                    ],
                    '_type' => 'recordset'
                ]
            ],
        's' => [
            ['n' => 'ContactData', 't' => 'Выборка']
        ],
        '_type' => 'record'
        ],
        'options' => null
    ],
    'id' => 1
];
$data_string = json_encode($data);
$cookiestring = ''; // put string of cookies here

$headers = [
  'authority: online.sbis.ru',
  'accept: application/json, text/javascript, */*; q=0.01',
  'accept-language: ru-RU;q=0.8,en-US;q=0.5,en;q=0.3',
  'content-type: application/json; charset=UTF-8',
  'cookie: '.$cookiestring,
  'referer: https://online.sbis.ru/page/dialogs',
  'sec-ch-ua: " Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
  'sec-ch-ua-mobile: ?0',
  'sec-ch-ua-platform: "Linux"',
  'sec-fetch-dest: empty',
  'sec-fetch-mode: cors',
  'sec-fetch-site: same-origin',
  'user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36',
  'x-calledmethod: '.$method,
  'x-lastmodification: 2022-04-26T183212.608699+03',
  'x-originalmethodname: '.base64_encode($method),
  'x-requested-with: XMLHttpRequest',
];
  
$ch = curl_init($url);
curl_setopt($ch, CURLOPT_VERBOSE, false); // for debug set true
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'POST');
curl_setopt($ch, CURLOPT_POSTFIELDS, $data_string);
curl_setopt($ch, CURLOPT_HEADER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$result = curl_exec($ch);
curl_close($ch);
if ($result) {
    var_dump($result);
} else {
    echo 'Something was wrong!'
}
?>
```

### Найти частное лицо по номеру телефона, в формате *.py

```python
//Пример поиска по телефону

requirejs(['Types/source'], function(blo){
new blo.SbisService({
    endpoint: {
        contract: 'CRMClients',
        address: '/service/?x_version=22.3100-709'
    }
}).call(
'GetCustomerByParams',
{
    "client_data": {
        "d": [
            {
                "d": [
                    [
                        "89151111111",
                        "mobile_phone",
                        null
                    ]
                ],
                "s": [
                    {
                        "t": "Строка",
                        "n": "Value"
                    },
                    {
                        "t": "Строка",
                        "n": "Type"
                    },
                    {
                        "t": "Строка",
                        "n": "Priority"
                    }
                ],
                "_type": "recordset"
            }
        ],
        "s": [
            {
                "n": "ContactData",
                "t": "Выборка"
            }
        ],
        "_type": "record"
    },
    "options": null
}
); //.addBoth(console.info);
});
```

## Создать частное лицо в Saby

Если в Saby CRM нет частного лица с нужными параметрами, создайте его. Выполните запрос.

### Структура запроса

Метод запроса: CRMClients.SaveCustomer

Адрес запроса: https://online.sbis.ru/service/

| Параметр | Тип | Описание |
|----------|-----|----------|
| UUID | uuid | Идентификатор клиента в сервисе профилей |
| CustomerID | Int | Идентификатор клиента в локальной схеме |
| Surname | text | Фамилия клиента |
| Name | text | Имя клиента |
| Patronymic | text | Отчество клиента |
| ContactData | recordSet | Набор записей формата таблицы «Contact» |
| SoftUpdate | bool | Флаг отсутствия необходимости обновления ФИО, по-умолчанию «true» |
| Gender | Int | Пол |
| Address | text | Адрес прописки |
| BirthDay | Date | День рождения |
| IdentityDocument | record | Запись с информацией о документе |

### Пример

```javascript
requirejs(['Types/source'], function(blo){
new blo.SbisService({
    endpoint: {
        contract: 'CRMClients',
        address: '/service/?x_version=20.7202-3'
    }
}).call(
'SaveCustomer',
{
    "CustomerData": {
        "d": [
            "Иванов",
            "Иван",
            "Иванович",
            0,
            "Адрес физического лица"
        ],
        "s": [
            {
                "n": "Surname",
                "t": "Строка"
            },
            {
                "n": "Name",
                "t": "Строка"
            },
            {
                "n": "Patronymic",
                "t": "Строка"
            },
            {
                "n": "Gender",
                "t": "Число целое"
            },
            {
                "n": "Address",
                "t": "Строка"
            }      
        ],
        "_type": "record",
        "f": 0
    }
}
); //.addBoth(console.info);
});
```
