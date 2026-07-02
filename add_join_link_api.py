with open("web_backend.py", "r") as f:
    content = f.read()

target_str = "    }\n\n\n@app.get(\"/admin-api/users\", dependencies=[Depends(require_admin)])"

new_api = """    }


@app.post("/admin-api/manual-orders/generate-join-link", dependencies=[Depends(require_admin)])
async def admin_generate_manual_join_link(request: Request):
    body = await request.json()
    order_id = str(body.get("order_id", "")).strip()
    telegram_user_id = str(body.get("telegram_user_id", "")).strip()
    plan_name = str(body.get("plan_name", "")).strip()
    full_name = str(body.get("full_name", "")).strip()
    expire_at_str = str(body.get("expire_at", "")).strip()
    activation_code = str(body.get("activation_code", "")).strip()
    
    if not order_id or not telegram_user_id or not plan_name:
        raise HTTPException(status_code=400, detail="Thiếu thông tin đơn hàng để tạo link (order_id, telegram_user_id, plan_name).")
        
    try:
        user_id = int(telegram_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Telegram ID phải là số.")
        
    from modules.mod_coupon import build_invite_links

    support_link, support_error = await create_support_invite_link(user_id)
    links_text = ""
    group_names = []
    failed_groups = []
    invite_results = []
    try:
        links_text, group_names, failed_groups, invite_results = await build_invite_links(user_id, plan_name)
    except Exception as exc:
        print(f"⚠️ Không build được join links cho manual order {order_id}: {exc}")
        
    if support_link:
        support_text = render_manual_order_support_text("💬 {support_group_name}:\\n{support_link}", {
            "order_id": order_id,
            "telegram_user_id": telegram_user_id,
            "full_name": full_name,
            "plan_name": plan_name,
            "expire_at": expire_at_str,
            "support_group_name": support_group_name(),
            "support_link": support_link,
            "support_error": "",
        })
    elif support_error:
        support_text = render_activation_text(
            "MANUAL_ORDER_SUPPORT_ERROR_TEMPLATE",
            "💬 {support_group_name}: Không tạo được link hỗ trợ ({support_error})",
            {
                "support_group_name": support_group_name(),
                "support_error": support_error,
            },
        )
    else:
        support_text = ""
        
    order_text = render_manual_order_info_text({
        "order_id": order_id,
        "telegram_user_id": telegram_user_id,
        "full_name": full_name or telegram_user_id,
        "plan_name": plan_name,
        "expire_at": expire_at_str,
    })
    
    join_template = str(db.get_config(
        "MANUAL_ORDER_JOIN_TEMPLATE",
        "{order_text}\\n\\n{bot_link_title}\\n{links_text}\\n\\n{bot_link_subtitle}\\n\\n{support_text}",
    ) or "").strip()
    
    activation_url = build_manual_activation_url(activation_code)
    
    manual_order_join_text = render_manual_order_message_text(join_template, {
        "order_id": order_id,
        "telegram_user_id": telegram_user_id,
        "full_name": full_name or telegram_user_id,
        "plan_name": plan_name,
        "expire_at": expire_at_str,
        "order_text": order_text,
        "bot_link_title": render_activation_text("MANUAL_ORDER_JOIN_LINK_TITLE", "💬 Link tham gia nhóm", {}),
        "bot_link_subtitle": render_activation_text("MANUAL_ORDER_JOIN_LINK_SUBTITLE", "Dùng tin này để gửi khách toàn bộ link tham gia nhóm trong đơn.", {}),
        "activation_url": activation_url,
        "message_url": "",
        "links_text": links_text,
        "support_text": support_text,
        "support_group_name": support_group_name(),
        "support_link": support_link,
        "support_error": support_error,
        "activation_code": activation_code,
    })
    
    return {
        "data": {
            "links_text": links_text,
            "support_text": support_text,
            "support_link": support_link,
            "support_error": support_error,
            "manual_order_join_text": manual_order_join_text
        }
    }


@app.get("/admin-api/users", dependencies=[Depends(require_admin)])"""

content = content.replace(target_str, new_api)

with open("web_backend.py", "w") as f:
    f.write(content)

print("Added new endpoint successfully.")
