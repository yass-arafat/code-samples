from .models import InformationDetail, InformationSection


def get_information_sections():
    info_sections = InformationSection.objects.filter(is_active=True)
    info_details = InformationDetail.objects.filter(is_active=True)

    sections_data = []
    for section in info_sections:
        pages_data = list(info_details.filter(section=section).values("id", "title"))
        sections_data.append({"name": section.title, "pages": pages_data})

    return {"sections": sections_data} if sections_data else None


def get_information_detail(info_detail_id):
    try:
        info_detail = InformationDetail.objects.get(id=info_detail_id)
    except InformationDetail.DoesNotExist:
        raise ValueError(f"No info details found with id {info_detail_id}")

    response_data = {"title": info_detail.title, "body": info_detail.body}
    return response_data
