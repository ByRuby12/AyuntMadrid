import json

# DICCIONARIOS DE AVISOS, PETICIONES, TEXTOS Y MAS
AVISOS_PRUEBA = {
    "Alumbrado Público": [
        {"nombre": "Calle Apagada", "id": ["591b3a514e4ea844018b457c"]},
        {"nombre": "Calle Apagada v2", "id": ["657883c9dd903d3f89075423"]},
        {"nombre": "Calle Apagada v4", "id": ["66583bc3070644ce03026ed3"]},
        {"nombre": "Farola Apagada", "id": ["591b3a194e4ea83a018b46bb"]},
        {"nombre": "Luces de Navidad", "id": ["654520fb19a50405480fdf8c"]},
        {"nombre": "Otras Averías de Alumbrado", "id": ["591b3b394e4ea83a018b46ca"]}
    ],
    "Aparcamiento Regulado": [
        {"nombre": "Aplicación Móvil", "id": ["5922eb0b4e4ea8002d8b4577"]},
        {"nombre": "Aviso de Denuncia", "id": ["591b08f24e4ea840018b456a", "591b08fd4e4ea839018b456e"]},
        {"nombre": "No Imprime tique o no valida Pin", "id": ["5922ea694e4ea8052d8b4567"]},
        {"nombre": "No permite anulación de denuncia", "id": ["5922e78f4e4ea83c178b4587"]},
        {"nombre": "Parquímetro", "id": ["5922e8414e4ea8fb2c8b4567"]},
        {"nombre": "Tarjeta Crédito atascada", "id": ["5922e9384e4ea8002d8b4567"]}
    ],
    "Arboles y Parques": [
        {"nombre": "Árbol en mal estado", "id": ["591b30844e4ea83a018b45fe"]},
        {"nombre": "Caminos no pavimentados", "id": ["591b32654e4ea83a018b4620"]},
        {"nombre": "Incidencias de riesgo", "id": ["591b31494e4ea83a018b460d"]},
        {"nombre": "Incidencias en alcorque o hueco", "id": ["591b31ad4e4ea839018b4632"]},
        {"nombre": "Plagas", "id": ["591b310d4e4ea840018b460e"]},
        {"nombre": "Poda de Árbol", "id": ["591b303b4e4ea840018b45ff"]},
        {"nombre": "Quitar maleza", "id": ["591b32234e4ea840018b461d"]},
        {"nombre": "Sustitución de Árbol", "id": ["591b30d14e4ea839018b4623"]}
    ],
    "Áreas Infantiles, Áreas de Mayores y circuitos": [
        {"nombre": "Área de Mayores y circuitos", "id": ["591ed1c04e4ea839018b457f"]},
        {"nombre": "Área Infantil", "id": ["591ed1314e4ea838018b457b"]}
    ],
    "Calzadas y Aceras": [
        {"nombre": "Alcantarillado", "id": ["591b36544e4ea839018b4653"]},
        {"nombre": "Desperfecto en acera", "id": ["591b375c4e4ea83a018b4686"]},
        {"nombre": "Desperfecto en calzada", "id": ["591b379e4e4ea844018b456d"]},
        {"nombre": "Hidrantes de bomberos", "id": ["591b36d14e4ea83a018b4678"]},
        {"nombre": "Otras incidencias en calzadas y aceras", "id": ["591b39334e4ea840018b4675"]},
        {"nombre": "Tapas de registro", "id": ["591b38484e4ea83a018b4695"]},
        {"nombre": "Tapa de Agua Isabel II", "id": ["5922ee3c4e4ea8152d8b4581"]}
    ],
    "Cubos y Contenedores": [
        {"nombre": "Cambio de tamaño de cubo", "id": ["591b11144e4ea839018b459c"]},
        {"nombre": "Cambio de ubicación de cubo o contenedor", "id": ["591b10404e4ea840018b4581"]},
        {"nombre": "Cubo o contenedor abandonado", "id": ["591b10b24e4ea840018b4599"]},
        {"nombre": "Cubo o contenedor en mal estado", "id": ["591b0eea4e4ea839018b4576"]},
        {"nombre": "Horquillas delimitadoras", "id": ["591b11c24e4ea839018b45b4"]},
        # {"nombre": "Nuevo cubo o contenedor", "id": ["591b0cf14e4ea840018b4573"]},
        {"nombre": "Vaciado de aceite", "id": ["63626c55f2e31df5178b457c"]},
        {"nombre": "Vaciado de cubo o contenedor", "id": ["591b0fd64e4ea839018b4584"]}
    ],
    "Fuentes": [
        {"nombre": "Incidencias en fuentes de Beber", "id": ["591b33494e4ea840018b462c"]},
        {"nombre": "Incidencias en fuentes ornamentales", "id": ["591b33da4e4ea83a018b464f"]}
    ],
    "Limpiezas y Pintadas": [
        {"nombre": "Limpieza en solares municipales", "id": ["591b167a4e4ea83a018b45c0"]},
        {"nombre": "Limpieza en vías públicas", "id": ["591b126d4e4ea840018b45b6"]},
        {"nombre": "Limpieza mobiliario urbano o áreas infantiles", "id": ["591b16204e4ea83a018b45ae"]},
        {"nombre": "Limpieza en zonas verdes", "id": ["591b15c14e4ea83a018b45a0"]},
        {"nombre": "Pintadas y Grafitis", "id": ["630f7c8e5b02a415138b4591"]},
        {"nombre": "SELUR", "id": ["5c5d466f850f3f301d8b4567"]}
    ],
    "Mobiliario Urbano": [
        {"nombre": "Banco", "id": ["591b3c6a4e4ea83a018b46ee"]},
        {"nombre": "Bolardo u horquilla", "id": ["591b3cd14e4ea844018b4599"]},
        {"nombre": "Otros", "id": ["59230a2e4e4ea83e018b458d"]},
        {"nombre": "Vallas", "id": ["591b3d4a4e4ea840018b46c4"]}
    ],
    "Papeleras": [
        {"nombre": "Falta de bolsas para excrementos caninos", "id": ["591b17914e4ea839018b45e8"]},
        {"nombre": "Mal estado de papelera", "id": ["591b18404e4ea83a018b45cf"]},
        # {"nombre": "Nueva Instalación de Papelera", "id": ["591b17e84e4ea840018b45c4"]},
        {"nombre": "Vaciado de Papelera", "id": ["591b176a4e4ea839018b45d9"]}
    ],
    "Plagas": [
        {"nombre": "Ratas y Cucarachas", "id": ["5b60529fed6abc0b2b8b45eb"]}
    ],
    "Retirada de Elementos": [
        {"nombre": "Animales muertos", "id": ["591b1f474e4ea83a018b45de"]},
        {"nombre": "Contenedor de ropa no autorizada", "id": ["591b20654e4ea840018b45e2"]},
        {"nombre": "Muebles abandonados en vía pública", "id": ["591b1eef4e4ea840018b45d3"]},
        {"nombre": "Muebles Particulares", "id": ["591b1e834e4ea839018b4605"]},
        {"nombre": "Recogida de saco o contenedor de escombros", "id": ["591b20c14e4ea83a018b45ef"]}
    ],
    "Señales y Semáforos": [
        {"nombre": "Incidencia en avisador acústico de semáforo", "id": ["591ed4db4e4ea844018b45a9"]},
        {"nombre": "Incidencia en Pulsador", "id": ["5b56e6bbfcf9f05f118b459f"]},
        {"nombre": "Incidencia en Señal", "id": ["591ed63e4e4ea844018b45b8"]},
        {"nombre": "Semáforo Apagado", "id": ["591ed3604e4ea838018b458a"]}
    ],
    "Vehículos Abandonados. Retirada de vehículo": [
        {"nombre": "Vehículos Abandonados. Retirada de vehículo", "id": ["591ed2774e4ea839018b4595"]}
    ]
}

# Diccionario de peticiones de mejora o nuevas instalaciones
PETICIONES_PRUEBA = {
    "Áreas Infantiles, Áreas de Mayores y circuitos": [
        {"nombre": "Nueva Instalación", "id": ["591ed08b4e4ea839018b4568"]}
    ],
    "Calzadas y Aceras": [
        {"nombre": "Mejora de Accesibilidad", "id": ["591b37fe4e4ea840018b4666"]}
    ],
    "Fuentes": [
        {"nombre": "Nueva Instalación de fuente de beber", "id": ["591b33064e4ea83a018b4640"]}
    ],
    "Mobiliario Urbano": [
        {"nombre": "Nueva Instalación", "id": ["591b3c014e4ea840018b46b0"]}
    ],
    "Señales y Semáforos": [
        {"nombre": "Nueva Señal", "id": ["591ed5b64e4ea839018b45b8"]}
    ],
    "Papeleras": [
        {"nombre": "Nueva Instalación de Papelera", "id": ["591b17e84e4ea840018b45c4"]}
    ],
     "Cubos y Contenedores": [
        {"nombre": "Nuevo cubo o contenedor", "id": ["591b0cf14e4ea840018b4573"]},
     ]
}

# Diccionario de textos del bot y mensajes de seguimiento 
BOT_TEXTS = {
    'es': {
        'detected': "✅ He detectado un {tipo} en la categoría '{categoria}' y subcategoría '{subcategoria}'.",
        'send_location': "Por favor, envíame la ubicación del incidente:",
        'send_media': "📸 Si quieres, ahora puedes enviar una *foto o video* del problema. Esto puede ayudar a los equipos del Ayuntamiento.",
        'skip_media': "O pulsa 'Omitir' para continuar sin archivo.",
        'followup': (
            "📋 Reporte Seguimiento: {service_request_id}\n"
            "👤 Usuario: `{usuario}`\n"
            "📌 Tipo: {tipo}\n"
            "📂 Categoría: {categoria}\n"
            "🔖 Subcategoría: {subcategoria}\n"
            "🗺️ Dirección: {latitud} {longitud}\n"
            "💬 Descripción: {descripcion}\n"
        ),
        'sent': "✅ Tu reporte ha sido enviado correctamente a la Plataforma del Ayuntamiento de Madrid",
        'out_of_madrid': "❌ No se puede enviar el aviso/petición porque la ubicación seleccionada está fuera de la ciudad de Madrid.\n\nSolo se pueden enviar reportes dentro del municipio de Madrid.",
        'no_report': "❌ No tengo datos del reporte. Inténtalo de nuevo.",
        'media_error': "❌ Por favor, envía una foto, un video o pulsa 'Omitir'.",
        'location_error': "❌ Por favor, envía una ubicación válida usando el botón correspondiente.",
        'skip_button': 'Omitir',
        'ayto_error': "⚠️ Error al enviar el reporte al Ayuntamiento. Pero se ha enviado correctamente al grupo."
    },
    'en': {
        'detected': "✅ I have detected a {tipo} in category '{categoria}' and subcategory '{subcategoria}.'",
        'send_location': "Please send me the location of the incident:",
        'send_media': "📸 If you want, you can now send a *photo or video* of the issue. This can help the City Council teams.",
        'skip_media': "Or press 'Skip' to continue without a file.",
        'followup': (
            "📋 Report Follow-up: {service_request_id}\n"
            "👤 User: `{usuario}`\n"
            "📌 Type: {tipo}\n"
            "📂 Category: {categoria}\n"
            "🔖 Subcategory: {subcategoria}\n"
            "🗺️ Address: {latitud} {longitud}\n"
            "💬 Description: {descripcion}\n"
        ),
        'sent': "✅ Your report has been successfully sent to the Madrid City Council platform",
        'out_of_madrid': "❌ The report cannot be sent because the selected location is outside the city of Madrid.\n\nReports can only be sent within the municipality of Madrid.",
        'no_report': "❌ I have no report data. Please try again.",
        'media_error': "❌ Please send a photo, a video, or press 'Skip'.",
        'location_error': "❌ Please send a valid location using the corresponding button.",
        'skip_button': 'Skip',
        'ayto_error': "⚠️ Error sending the report to the City Council. But it has been sent to the group."
    },
    'fr': {
        'detected': "✅ J'ai détecté un {tipo} dans la catégorie '{categoria}' et la sous-catégorie '{subcategoria}'.",
        'send_location': "Veuillez m'envoyer l'emplacement de l'incident :",
        'send_media': "📸 Si vous le souhaitez, vous pouvez maintenant envoyer une *photo ou une vidéo* du problème. Cela peut aider les équipes de la Mairie.",
        'skip_media': "Ou appuyez sur 'Ignorer' pour continuer sans fichier.",
        'followup': (
            "📋 Suivi du rapport : {service_request_id}\n"
            "👤 Utilisateur : `{usuario}`\n"
            "📌 Type : {tipo}\n"
            "📂 Catégorie : {categoria}\n"
            "🔖 Sous-catégorie : {subcategoria}\n"
            "🗺️ Adresse : {latitud} {longitud}\n"
            "💬 Description : {descripcion}\n"
        ),
        'sent': "✅ Votre rapport a été envoyé avec succès à la plateforme de la Mairie de Madrid",
        'out_of_madrid': "❌ Le rapport ne peut pas être envoyé car l'emplacement sélectionné est en dehors de la ville de Madrid.\n\nLes rapports ne peuvent être envoyés que dans la municipalité de Madrid.",
        'no_report': "❌ Je n'ai pas de données de rapport. Veuillez réessayer.",
        'media_error': "❌ Veuillez envoyer une photo, une vidéo ou appuyer sur 'Ignorer'.",
        'location_error': "❌ Veuillez envoyer un emplacement valide en utilisant le bouton correspondant.",
        'skip_button': 'Ignorer',
        'ayto_error': "⚠️ Erreur lors de l'envoi du rapport à la Mairie. Mais il a été envoyé au groupe."
    },
    'de': {
        'detected': "✅ Ich habe ein {tipo} in der Kategorie '{categoria}' und Unterkategorie '{subcategoria}' erkannt.",
        'send_location': "Bitte sende mir den Standort des Vorfalls:",
        'send_media': "📸 Wenn du möchtest, kannst du jetzt ein *Foto oder Video* des Problems senden. Das kann den Teams der Stadtverwaltung helfen.",
        'skip_media': "Oder drücke 'Überspringen', um ohne Datei fortzufahren.",
        'followup': (
            "📋 Bericht Nachverfolgung: {service_request_id}\n"
            "👤 Nutzer: `{usuario}`\n"
            "📌 Typ: {tipo}\n"
            "📂 Kategorie: {categoria}\n"
            "🔖 Unterkategorie: {subcategoria}\n"
            "🗺️ Adresse: {latitud} {longitud}\n"
            "💬 Beschreibung: {descripcion}\n"
        ),
        'sent': "✅ Dein Bericht wurde erfolgreich an die Plattform der Stadt Madrid gesendet",
        'out_of_madrid': "❌ Der Bericht kann nicht gesendet werden, da der ausgewählte Standort außerhalb von Madrid liegt.\n\nBerichte können nur innerhalb der Gemeinde Madrid gesendet werden.",
        'no_report': "❌ Keine Berichtsdaten vorhanden. Bitte versuche es erneut.",
        'media_error': "❌ Bitte sende ein Foto, ein Video oder drücke 'Überspringen'.",
        'location_error': "❌ Bitte sende einen gültigen Standort über den entsprechenden Button.",
        'skip_button': 'Überspringen',
        'ayto_error': "⚠️ Fehler beim Senden des Berichts an die Stadtverwaltung. Aber er wurde an die Gruppe gesendet."
    },
    'zh': {
        'detected': "✅ 我已检测到类别为'{categoria}'、子类别为'{subcategoria}'的{tipo}。",
        'send_location': "请发送事件的位置：",
        'send_media': "📸 如果需要，现在可以发送问题的*照片或视频*，这有助于市政团队。",
        'skip_media': "或点击“跳过”以继续，无需文件。",
        'followup': (
            "📋 跟进编号: {service_request_id}\n"
            "👤 用户: `{usuario}`\n"
            "📌 类型: {tipo}\n"
            "📂 类别: {categoria}\n"
            "🔖 子类别: {subcategoria}\n"
            "🗺️ 地址: {latitud} {longitud}\n"
            "💬 描述: {descripcion}\n"
        ),
        'sent': "✅ 您的报告已成功发送至马德里市政平台",
        'out_of_madrid': "❌ 由于所选位置不在马德里市内，无法发送报告。\n\n只能在马德里市内发送报告。",
        'no_report': "❌ 没有报告数据。请重试。",
        'media_error': "❌ 请发送照片、视频或点击“跳过”。",
        'location_error': "❌ 请使用相应按钮发送有效的位置。",
        'skip_button': '跳过',
        'ayto_error': "⚠️ 报告发送到市政平台时出错，但已成功发送到群组。"
    },
    'pt': {
        'detected': "✅ Eu detectei um {tipo} na categoria '{categoria}' e subcategoria '{subcategoria}'.",
        'send_location': "Por favor, envie-me a localização do incidente:",
        'send_media': "📸 Se quiser, agora você pode enviar uma *foto ou vídeo* do problema. Isso pode ajudar as equipes da Prefeitura.",
        'skip_media': "Ou pressione 'Pular' para continuar sem um arquivo.",
        'followup': (
            "📋 Acompanhamento do relatório: {service_request_id}\n"
            "👤 Usuário: `{usuario}`\n"
            "📌 Tipo: {tipo}\n"
            "📂 Categoria: {categoria}\n"
            "🔖 Subcategoria: {subcategoria}\n"
            "🗺️ Endereço: {latitud} {longitud}\n"
            "💬 Descrição: {descripcion}\n"
        ),
        'sent': "✅ Seu relatório foi enviado com sucesso para a plataforma da Prefeitura de Madrid",
        'out_of_madrid': "❌ O relatório não pode ser enviado porque a localização selecionada está fora da cidade de Madrid.\n\nOs relatórios só podem ser enviados dentro do município de Madrid.",
        'no_report': "❌ Não tenho dados do relatório. Por favor, tente novamente.",
        'media_error': "❌ Por favor, envie uma foto, um vídeo ou clique em 'Pular'.",
        'location_error': "❌ Por favor, envie uma localização válida usando o botão correspondente.",
        'skip_button': 'Pular',
        'ayto_error': "⚠️ Erro ao enviar o relatório para a Prefeitura. Mas foi enviado para o grupo."
    },
    'it': {
        'detected': "✅ Ho rilevato un {tipo} nella categoria '{categoria}' e sottocategoria '{subcategoria}.'",
        'send_location': "Per favore, inviami la posizione dell'incidente:",
        'send_media': "📸 Se vuoi, ora puoi inviare una *foto o video* del problema. Questo può aiutare le squadre del Comune.",
        'skip_media': "Oppure premi 'Salta' per continuare senza file.",
        'followup': (
            "📋 Seguito della segnalazione: {service_request_id}\n"
            "👤 Utente: `{usuario}`\n"
            "📌 Tipo: {tipo}\n"
            "📂 Categoria: {categoria}\n"
            "🔖 Sottocategoria: {subcategoria}\n"
            "🗺️ Indirizzo: {latitud} {longitud}\n"
            "💬 Descrizione: {descripcion}\n"
        ),
        'sent': "✅ La tua segnalazione è stata inviata con successo alla piattaforma del Comune di Madrid",
        'out_of_madrid': "❌ La segnalazione non può essere inviata perché la posizione selezionata è fuori dalla città di Madrid.\n\nLe segnalazioni possono essere inviate solo all'interno del comune di Madrid.",
        'no_report': "❌ Nessun dato della segnalazione. Riprova.",
        'media_error': "❌ Per favore, invia una foto, un video o premi 'Salta'.",
        'location_error': "❌ Per favore, invia una posizione valida usando il pulsante corrispondente.",
        'skip_button': 'Salta',
        'ayto_error': "⚠️ Errore nell'invio della segnalazione al Comune. Ma è stata inviata al gruppo."
    },
    'ar': {
        'detected': "✅ لقد اكتشفت {tipo} في الفئة '{categoria}' والفئة الفرعية '{subcategoria}'.",
        'send_location': "يرجى إرسال موقع الحادث:",
        'send_media': "📸 إذا أردت، يمكنك الآن إرسال *صورة أو فيديو* للمشكلة. هذا يمكن أن يساعد فرق البلدية.",
        'skip_media': "أو اضغط 'تخطي' للمتابعة بدون ملف.",
        'followup': (
            "📋 متابعة التقرير: {service_request_id}\n"
            "👤 المستخدم: `{usuario}`\n"
            "📌 النوع: {tipo}\n"
            "📂 الفئة: {categoria}\n"
            "🔖 الفئة الفرعية: {subcategoria}\n"
            "🗺️ العنوان: {latitud} {longitud}\n"
            "💬 الوصف: {descripcion}\n"
        ),
        'sent': "✅ تم إرسال تقريرك بنجاح إلى منصة بلدية مدريد",
        'out_of_madrid': "❌ لا يمكن إرسال التقرير لأن الموقع المحدد خارج مدينة مدريد.\n\nيمكن إرسال التقارير فقط ضمن بلدية مدريد.",
        'no_report': "❌ لا توجد بيانات للتقرير. يرجى المحاولة مرة أخرى.",
        'media_error': "❌ يرجى إرسال صورة أو فيديو أو الضغط على 'تخطي'.",
        'location_error': "❌ يرجى إرسال موقع صالح باستخدام الزر المناسب.",
        'skip_button': 'تخطي',
        'ayto_error': "⚠️ حدث خطأ أثناء إرسال التقرير إلى البلدية. لكنه أُرسل إلى المجموعة."
    },
    'ru': {
        'detected': "✅ Обнаружен {tipo} в категории '{categoria}' и подкатегории '{subcategoria}'.",
        'send_location': "Пожалуйста, отправьте местоположение инцидента:",
        'send_media': "📸 Если хотите, вы можете отправить *фото или видео* проблемы. Это поможет городским службам.",
        'skip_media': "Или нажмите 'Пропустить', чтобы продолжить без файла.",
        'followup': (
            "📋 Отслеживание отчёта: {service_request_id}\n"
            "👤 Пользователь: `{usuario}`\n"
            "📌 Тип: {tipo}\n"
            "📂 Категория: {categoria}\n"
            "🔖 Подкатегория: {subcategoria}\n"
            "🗺️ Адрес: {latitud} {longitud}\n"
            "💬 Описание: {descripcion}\n"
        ),
        'sent': "✅ Ваш отчёт успешно отправлен на платформу муниципалитета Мадрида",
        'out_of_madrid': "❌ Невозможно отправить отчёт, так как выбранное местоположение вне города Мадрид.\n\nОтчёты можно отправлять только в пределах муниципалитета Мадрид.",
        'no_report': "❌ Нет данных отчёта. Пожалуйста, попробуйте снова.",
        'media_error': "❌ Пожалуйста, отправьте фото, видео или нажмите 'Пропустить'.",
        'location_error': "❌ Пожалуйста, отправьте действительное местоположение с помощью соответствующей кнопки.",
        'skip_button': 'Пропустить',
        'ayto_error': "⚠️ Ошибка при отправке отчёта в муниципалитет. Но он был отправлен в группу."
    },
    'hi': {
        'detected': "✅ मैंने '{categoria}' श्रेणी और '{subcategoria}' उपश्रेणी में एक {tipo} पाया है।",
        'send_location': "कृपया घटना का स्थान भेजें:",
        'send_media': "📸 यदि आप चाहें, तो अब आप समस्या की *फोटो या वीडियो* भेज सकते हैं। यह नगर निगम की टीमों की मदद कर सकता है।",
        'skip_media': "या 'छोड़ें' दबाएँ बिना फ़ाइल के जारी रखने के लिए।",
        'followup': (
            "📋 रिपोर्ट फॉलोअप: {service_request_id}\n"
            "👤 उपयोगकर्ता: `{usuario}`\n"
            "📌 प्रकार: {tipo}\n"
            "📂 श्रेणी: {categoria}\n"
            "🔖 उपश्रेणी: {subcategoria}\n"
            "🗺️ पता: {latitud} {longitud}\n"
            "💬 विवरण: {descripcion}\n"
        ),
        'sent': "✅ आपकी रिपोर्ट सफलतापूर्वक मैड्रिड नगर निगम प्लेटफॉर्म पर भेज दी गई है",
        'out_of_madrid': "❌ चयनित स्थान मैड्रिड शहर के बाहर है, इसलिए रिपोर्ट नहीं भेजी जा सकती।\n\nरिपोर्ट केवल मैड्रिड नगर क्षेत्र के भीतर भेजी जा सकती है।",
        'no_report': "❌ रिपोर्ट डेटा उपलब्ध नहीं है। कृपया पुनः प्रयास करें।",
        'media_error': "❌ कृपया एक फोटो, वीडियो भेजें या 'छोड़ें' दबाएँ।",
        'location_error': "❌ कृपया संबंधित बटन का उपयोग करके एक मान्य स्थान भेजें।",
        'skip_button': 'छोड़ें',
        'ayto_error': "⚠️ रिपोर्ट नगर निगम को भेजने में त्रुटि। लेकिन यह समूह में भेज दी गई है।"
    },
}

# Diccionario de mensajes de bienvenida en varios idiomas 
WELCOME_MESSAGES = {
    'es': [
        "👋 Hola, buenas {usuario}. No hemos podido reconocer el contenido del mensaje o la foto. 😕",
        "✍️ Por favor, describe brevemente el problema o envía una foto para poder clasificarlo:"
    ],
    'en': [
        "👋 Hello {usuario}, we couldn't recognize the content of your message or photo. 😕",
        "✍️ Please briefly describe the problem or send a photo so we can classify it."
    ],
    'fr': [
        "👋 Bonjour {usuario}, nous n'avons pas pu reconnaître le contenu du message ou de la photo. 😕",
        "✍️ Veuillez décrire brièvement le problème ou envoyer une photo pour que nous puissions le classer."
    ],
    'de': [
        "👋 Hallo {usuario}, wir konnten den Inhalt der Nachricht oder des Fotos nicht erkennen. 😕",
        "✍️ Bitte beschreibe das Problem kurz oder sende ein Foto, damit wir es klassifizieren können."
    ],
    'zh': [
        "👋 您好，{usuario}。我们无法识别您的消息或照片内容。😕",
        "✍️ 请简要描述问题或发送一张照片，以便我们进行分类。"
    ],
    'pt': [
        "👋 Olá {usuario}, não conseguimos reconhecer o conteúdo da mensagem или foto. 😕",
        "✍️ Por favor, descreva brevemente o problema ou envie uma foto para que possamos classificá-lo."
    ],
    'it': [
        "👋 Ciao {usuario}, non siamo riusciti a riconoscere il contenuto del messaggio o della foto. 😕",
        "✍️ Per favore, descrivi brevemente il problema o invia una foto per poterlo classificare."
    ],
    'ar': [
        "👋 مرحبًا {usuario}، لم نتمكن من التعرف على محتوى الرسالة أو الصورة. 😕",
        "✍️ يرجى وصف المشكلة بإيجاز أو إرسال صورة حتى نتمكن من تصنيفها."
    ],
    'ru': [
        "👋 Здравствуйте, {usuario}. Мы не смогли распознать содержимое сообщения или фото. 😕",
        "✍️ Пожалуйста, кратко опишите проблему или отправьте фото для классификации."
    ],
    'hi': [
        "👋 नमस्ते {usuario}, हम आपके संदेश या फोटो की सामग्री को पहचान नहीं सके। 😕",
        "✍️ कृपया समस्या का संक्षिप्त विवरण दें या एक फोटो भेजें ताकि हम उसे वर्गीकृत कर सकें।"
    ]
}

# Prompt del sistema 
system_content_prompt = f"""
Eres un asistente del Ayuntamiento de Madrid encargado de clasificar reportes ciudadanos.
El usuario puede enviarte un mensaje de texto o una imagen (foto).

🔎 Si recibes una imagen, analiza su contenido visual (no solo el nombre del archivo o metadatos). Si la imagen contiene texto visible, analízalo también. No asumas categorías por contexto externo, solo por lo que se observa visualmente en la imagen y lo que está en los diccionarios.

Los reportes pueden ser de tipo 'aviso' (problemas o incidencias) o 'petición' (solicitudes de mejora).
Debes analizar el mensaje o la imagen del usuario e identificar su tipo ('aviso' o 'petición'), una categoría y una subcategoría,
siguiendo estrictamente los valores que aparecen en los diccionarios oficiales del Ayuntamiento.

IMPORTANTE: El mensaje o la imagen del usuario puede estar relacionado con cualquier idioma (español, inglés, francés, alemán, etc). Debes traducir internamente si es necesario y responder SIEMPRE en español, usando los nombres de categoría y subcategoría tal como aparecen en los diccionarios.

Cada categoría contiene una lista de subcategorías, y cada subcategoría tiene un campo "nombre" que debes usar como referencia exacta para clasificar.

Aquí tienes el listado completo de categorías y subcategorías válidas:

Categorías y subcategorías para AVISOS:
{json.dumps(AVISOS_PRUEBA, indent=2, ensure_ascii=False)}

Categorías y subcategorías para PETICIONES:
{json.dumps(PETICIONES_PRUEBA, indent=2, ensure_ascii=False)}

🔍 INSTRUCCIONES CRÍTICAS:
- El tipo ('aviso' o 'petición') debe determinarse exclusivamente según en qué diccionario (AVISOS o PETICIONES) se encuentre la categoría y subcategoría.
- NO asumas el tipo por palabras como 'solicito', 'quiero', etc.
- Si una subcategoría solo está en AVISOS, entonces el tipo debe ser 'aviso'.
- Si está solo en PETICIONES, entonces el tipo debe ser 'petición'.
- No inventes categorías ni subcategorías. Usa únicamente las que aparecen en los diccionarios proporcionados.

🚫 ERROR COMÚN (NO LO COMETAS):
- Mensaje: 'Solicito cubo de basura' → Subcategoría: 'Nuevo cubo o contenedor' (está en AVISOS) → Tipo correcto: 'aviso' (¡NO 'petición'!).

⚠️ RESPUESTA: Devuelve solo un JSON válido en este formato:
{{"tipo": "aviso", "categoría": "Alumbrado Público", "subcategoría": "Calle Apagada"}}

# ATENCIÓN: SI LA IMAGEN O EL MENSAJE NO PERMITEN IDENTIFICAR DE FORMA CLARA Y VISUAL UNA CATEGORÍA Y SUBCATEGORÍA EXACTA DE LOS DICCIONARIOS, RESPONDE ÚNICAMENTE CON UN JSON VACÍO: {{}}
# NO INCLUYAS NINGÚN TEXTO ADICIONAL, NI CAMPOS VACÍOS, NI EXPLICACIONES, NI CAMPOS CON CADENAS VACÍAS. SOLO EL JSON VACÍO: {{}}

# Además, detecta el idioma principal del mensaje del usuario y añade un campo 'idioma' (código ISO 639-1, por ejemplo 'es', 'en', 'fr', etc.) al JSON de respuesta. Ejemplo de respuesta: {{'tipo': 'aviso', 'categoría': 'Limpieza', 'subcategoría': 'Basura', 'idioma': 'es'}}
"""