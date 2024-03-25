# usage

```c
//components/amp/engine/duktape_engine/addons/network/http/module_http.c

char customer_header[HTTP_HEADER_SIZE] = {0};
char rsp_buf[HTTP_BUFF_SIZE];
char req_buf[HTTP_BUFF_SIZE];

/* create task for http download */
static void task_http_download_func(void *arg)
{
    httpclient_t client = {0};
    httpclient_data_t client_data = {0};
    http_param_t *param = (http_param_t *)arg;
    int num=0;
    int ret;

    char * req_url = "http://wangguan-498.oss-cn-beijing.aliyuncs.com/SHOPAD/public/mould5.png";
    int fd = aos_open("/data/http_text.png",  O_CREAT | O_RDWR | O_APPEND);

    memset(rsp_buf, 0, sizeof(rsp_buf));
    client_data.response_buf = rsp_buf;
    client_data.response_buf_len = sizeof(rsp_buf);

    ret = httpclient_conn(&client, req_url);

    if (!ret) {
        ret = httpclient_send(&client, req_url, HTTP_GET, &client_data);

        do{
            ret = httpclient_recv(&client, &client_data);//每次读取HTTP_BUFF_SIZE长度的数据
            printf("response_content_len=%d, retrieve_len=%d,content_block_len=%d\n", client_data.response_content_len,client_data.retrieve_len,client_data.content_block_len);
            printf("ismore=%d \n", client_data.is_more);

            num = aos_write(fd, client_data.response_buf, client_data.content_block_len);
            if(num > 0){
                printf("aos_write num=%d\n", num);
            }
        }while(client_data.is_more);//is_more为false表示全部数据接收完成
    }
    ret = aos_sync(fd);
    param->buffer = "http download success";
    httpclient_clse(&client);

    amp_task_schedule_call(http_request_notify, param);
    aos_task_exit(0);
}

/* create task for http request */
static void task_http_request_func(void *arg)
{
    char *url = NULL;
    uint32_t timeout = 0;
    int http_method = 0;
    int i = 0;
    int ret = 0;
    httpclient_t client = {0};
    httpclient_data_t client_data = {0};
    http_param_t *param = (http_param_t *)arg;

    url = param->url;
    timeout = param->timeout;
    http_method = param->method;

    amp_debug(MOD_STR, "task_http_request_func url: %s", url);
    amp_debug(MOD_STR, "task_http_request_func method: %d", http_method);
    amp_debug(MOD_STR, "task_http_request_func timeout: %d", timeout);

    memset(rsp_buf, 0, HTTP_BUFF_SIZE);
    client_data.response_buf = rsp_buf;
    client_data.response_buf_len = sizeof(rsp_buf);
    aos_msleep(50); /* need do things after state changed in main task */

    for (i = 0; i < http_header_index; i++) {
        httpc_construct_header(customer_header, HTTP_HEADER_SIZE, param->http_header[i].name, param->http_header[i].data);
    }
    http_header_index = 0;
    httpclient_set_custom_header(&client, customer_header);


    if(http_method == HTTP_GET){
        amp_info(MOD_STR,"http GET request=%s,timeout=%d\r\n", url, timeout);
        ret = httpclient_get(&client, url, &client_data);
        if( ret >= 0 ) {
            amp_info(MOD_STR,"GET Data received: %s, len=%d \r\n", client_data.response_buf, client_data.response_buf_len);
            strcpy(param->buffer,client_data.response_buf);
        }
    }else if(http_method == HTTP_POST){
        amp_info(MOD_STR,"http POST request=%s,post_buf=%s,timeout=%d\r\n", url,param->params,timeout);
        memset(req_buf, 0, sizeof(req_buf));
        strcpy(req_buf, "tab_index=0&count=3&group_id=6914830518563373582&item_id=6914830518563373581&aid=1768");
        client_data.post_buf = req_buf;
        client_data.post_buf_len = sizeof(req_buf);
        client_data.post_content_type="application/x-www-form-urlencoded";
        ret = httpclient_post(&client, "https://www.ixigua.com/tlb/comment/article/v5/tab_comments/", &client_data);
        if( ret >= 0 ) {
            amp_info(MOD_STR,"POST Data received: %s, len=%d \r\n", client_data.response_buf, client_data.response_buf_len);
            strcpy(param->buffer,client_data.response_buf);
        }
    }else if(http_method == HTTP_PUT){
        amp_info(MOD_STR,"http PUT request=%s,data=%s,timeout=%d\r\n", url,param->params,timeout);
        client_data.post_buf = param->params;
        client_data.post_buf_len = param->params_len;
        ret = httpclient_put(&client, url, &client_data);
        if( ret >= 0 ) {
            amp_info(MOD_STR,"Data received: %s, len=%d \r\n", client_data.response_buf, client_data.response_buf_len);
            strcpy(param->buffer,client_data.response_buf);
        }
    }else{
        ret = httpclient_get(&client, url, &client_data);
        if( ret >= 0 ) {
            amp_info(MOD_STR,"Data received: %s, len=%d \r\n", client_data.response_buf, client_data.response_buf_len);
            strcpy(param->buffer,client_data.response_buf);
        }
    }

    amp_task_schedule_call(http_request_notify, param);
    aos_task_exit(0);

    return;
}
```
